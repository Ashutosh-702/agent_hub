"""
Agent SDK + Coresignal MCP Query Processor

Replaces the entire LLM generation logic and query parsing pipeline.
Uses OpenAI Agent SDK with o3 model and Coresignal MCP for company search.
"""
import logging
import os
import re
from agents import Agent, Runner, ModelSettings
from agents.mcp.server import MCPServerSse
from openai.types import Reasoning

from ..core.models import CoreSignalMCPResponse, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)


class AgentMCPQueryProcessor:
    """
    Processes natural language queries using Agent SDK with Coresignal MCP.
    """
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.coresignal_api_key = os.getenv('CORESIGNAL_API_KEY')
        if not self.coresignal_api_key:
            raise ValueError("CORESIGNAL_API_KEY environment variable not set")
        self.model = "o3"
        self.reasoning_effort = Reasoning(effort="low")
        
        self.system_instructions = self._build_system_instructions()

        logger.info(f"AgentMCPQueryProcessor initialized with {self.model} model and Coresignal MCP")

    def _build_system_instructions(self) -> str:
        return """You are a structured search assistant. Interpret natural language queries, extract filters, use the appropriate tool, and return the required number of matching companies efficiently.
                Also use the Coresignal MCP to search for companies based on the query. 
        CRITICAL: ONLY one search call is allowed per query.
Important Instructions:
- Immediately extract the intent and filters from the query.
- Select and invoke a tool on the first reasoning turn — do not loop through tools or retry.
- Stop after you retrieve the required number of companies.
- Never ask clarifying questions or perform additional reasoning once the result is available.
- Do not generate summaries, explanations, or additional commentary.
- Keep responses strictly minimal and structured.

Output Constraints:
- Do not return more companies than requested.
- Descriptions should avoid fluff, intros, or generic phrases.
- Do not use bullet points, markdown, headings, or extra fields.
- Do not include reasoning, notes, or conclusions — only the list of company objects.

You must behave like an efficient search operator
"""

    async def process_query(self, search_request: SearchRequest) -> SearchResponse:
        """
        Process a search request using Agent SDK with Coresignal MCP.
        
        Args:
            search_request: Validated search request
            
        Returns:
            SearchResponse with companies and metadata
            
        Raises:
            Exception: If processing fails
        """
        try:
            logger.info(f"Processing query: {search_request.query}")

            coresignal_mcp = await self._setup_coresignal_mcp()
            
            agent = Agent(
                name="CompanySearchAgent",
                model=self.model,
                model_settings=ModelSettings(
                    reasoning=self.reasoning_effort,
                    extra_body={"service_tier":"flex"}
                ),
                mcp_servers=[coresignal_mcp],
                instructions=self.system_instructions,
                output_type=CoreSignalMCPResponse
            )
            
            user_prompt = self._build_user_prompt(search_request)
            
            logger.info(f"Starting Agent SDK search for: {search_request.query}")
            
            result = await Runner.run(
                starting_agent=agent,
                input=user_prompt
            )
            
            total_tokens = 0
            if hasattr(result, 'usage_summary') and result.usage_summary:
                input_tokens = getattr(result.usage_summary, 'input_tokens', 0)
                output_tokens = getattr(result.usage_summary, 'output_tokens', 0)
                total_tokens = input_tokens + output_tokens
                logger.info(f"API Usage: {total_tokens:,} tokens (input: {input_tokens:,}, output: {output_tokens:,})")
            
            mcp_response = result.final_output
            if not isinstance(mcp_response, CoreSignalMCPResponse):
                if hasattr(mcp_response, 'model_dump'):
                    mcp_data = mcp_response.model_dump()
                else:
                    mcp_data = dict(mcp_response) if hasattr(mcp_response, '__dict__') else {}
                mcp_response = CoreSignalMCPResponse(**mcp_data)
            
            search_response = self._convert_to_search_response(
                mcp_response, search_request, total_tokens
            )

            logger.info(f"Successfully processed query and found {len(mcp_response.companies)} companies")
            try:
                await coresignal_mcp.cleanup()
            except Exception as cleanup_error:
                logger.warning(f"MCP cleanup error: {cleanup_error}")
            return search_response

        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            return self._create_error_response(search_request, str(e))

    async def _setup_coresignal_mcp(self) -> MCPServerSse:
        """Set up Coresignal MCP server connection"""
        try:
            mcp_server = MCPServerSse(
                params={
                    "url": "https://mcp.coresignal.com/sse",
                    "headers": {"apikey": self.coresignal_api_key}
                },
                cache_tools_list=True
            )

            await mcp_server.connect()
            logger.debug("Coresignal MCP server started successfully")
            return mcp_server

        except Exception as e:
            logger.error(f"Failed to setup Coresignal MCP: {str(e)}")
            raise Exception(f"Coresignal MCP setup failed: {str(e)}")

    def _build_user_prompt(self, search_request: SearchRequest) -> str:
        return f"""
Using the system instructions provided earlier, complete the following task:\n
Query: "{search_request.query}"

Find companies matching this query: "{search_request.query}".

Return matching companies with their name and description. No retries, summaries, or commentary.
"""

    def _convert_to_search_response(self,
                                    mcp_response: CoreSignalMCPResponse,
                                    search_request: SearchRequest,
                                    total_tokens: int) -> SearchResponse:
        """Convert CoreSignalMCPResponse to SearchResponse format"""
        companies_data = []
        for company in mcp_response.companies:
            companies_data.append({
                "name": company.name,
                "description": company.description
            })

        return SearchResponse(
            search_id="mcp_" + str(hash(search_request.query))[:8],
            query={
                "original_query": search_request.query,
                "search_method": "agent_sdk_coresignal_mcp"
            },
            results={
                "companies": companies_data
            },
            metadata={
                "processing_method": "agent_sdk_mcp",
                "model_used": self.model,
                "reasoning_effort": self.reasoning_effort,
                "tokens_used": total_tokens,
                "mcp_server": "coresignal",
                "output_format": search_request.output_format
            }
        )

    def _create_error_response(self, search_request: SearchRequest, error_message: str) -> SearchResponse:
        """Create error response when processing fails"""
        return SearchResponse(
            search_id="error_" + str(hash(search_request.query))[:8],
            query={
                "original_query": search_request.query,
                "search_method": "agent_sdk_coresignal_mcp"
            },
            results={
                "companies": []
            },
            metadata={
                "processing_method": "agent_sdk_mcp",
                "model_used": self.model,
                "error": error_message,
                "output_format": search_request.output_format
            }
        )
