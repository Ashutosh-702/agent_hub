"""
Agent SDK + Coresignal MCP Query Processor

Replaces the entire LLM generation logic and query parsing pipeline.
Uses OpenAI Agent SDK with o3 model and Coresignal MCP for company search.
"""
import logging
import os
from typing import Dict, Any, Optional

from agents import Agent, Runner, ModelSettings
from agents.mcp.server import MCPServerStdio,MCPServerSse
from openai.types import Reasoning

from ..core.models import CoreSignalMCPResponse, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)


class AgentMCPQueryProcessor:
    """
    Processes natural language queries using Agent SDK with Coresignal MCP.
    Replaces EntityExtractor + DSLBuilder + LLMDSLGenerator entirely.
    """

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        
        # Validate environment
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.coresignal_api_key = os.getenv('CORESIGNAL_API_KEY')
        if not self.coresignal_api_key:
            raise ValueError("CORESIGNAL_API_KEY environment variable not set")
        
        # Model configuration - use faster model for better performance
        self.model = "o3"  # Much faster than o3
        self.reasoning_effort = "low"
        
        # System instructions for the agent
        self.system_instructions = self._build_system_instructions()
        
        logger.info(f"AgentMCPQueryProcessor initialized with {self.model} model and Coresignal MCP")

    def _build_system_instructions(self) -> str:
        return """You are a structured search assistant for a company intelligence platform. Your role is to interpret natural language queries and retrieve matching companies using available tools.

Your task is to extract structured filters from the query, call the most relevant tool, and return only the required number of companies efficiently.
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
            
            # Set up Coresignal MCP server
            coresignal_mcp = await self._setup_coresignal_mcp()
            
            # Create agent with optimized settings for speed
            agent = Agent(
                name="CompanySearchAgent", 
                model=self.model,
                model_settings=ModelSettings(
                    reasoning=Reasoning(effort="low")
                ),
                mcp_servers=[coresignal_mcp],
                instructions=self.system_instructions,
                output_type=CoreSignalMCPResponse
            )
            
            # Build user prompt
            user_prompt = self._build_user_prompt(search_request)
            
            # Log the request
            logger.info(f"Starting Agent SDK search for: {search_request.query}")
            logger.debug(f"Max results: {search_request.max_results}")
            
            # Run the agent with minimal turns
            result = await Runner.run(
                starting_agent=agent,
                input=user_prompt,
                max_turns=10
            )
            
            # Log token usage if available
            total_tokens = 0
            if hasattr(result, 'usage_summary') and result.usage_summary:
                input_tokens = getattr(result.usage_summary, 'input_tokens', 0)
                output_tokens = getattr(result.usage_summary, 'output_tokens', 0)
                total_tokens = input_tokens + output_tokens
                logger.info(f"API Usage: {total_tokens:,} tokens (input: {input_tokens:,}, output: {output_tokens:,})")
            
            # Process the structured response
            mcp_response = result.final_output
            if not isinstance(mcp_response, CoreSignalMCPResponse):
                if hasattr(mcp_response, 'model_dump'):
                    mcp_data = mcp_response.model_dump()
                else:
                    mcp_data = dict(mcp_response) if hasattr(mcp_response, '__dict__') else {}
                mcp_response = CoreSignalMCPResponse(**mcp_data)
            
            # Convert to SearchResponse format
            search_response = self._convert_to_search_response(
                mcp_response, search_request, total_tokens
            )
            
            logger.info(f"Successfully processed query and found {len(mcp_response.companies)} companies")
            return search_response
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            return self._create_error_response(search_request, str(e))
        
        finally:
            # Cleanup MCP connection
            if 'coresignal_mcp' in locals():
                try:
                    await coresignal_mcp.cleanup()
                except Exception as cleanup_error:
                    logger.warning(f"MCP cleanup error: {cleanup_error}")

    async def _setup_coresignal_mcp(self) -> MCPServerSse:
        """Set up Coresignal MCP server connection"""
        try:
            # Configure Coresignal MCP server
            # Based on the Coresignal MCP documentation
            
            # mcp_server = MCPServerStdio(
            #     params={
            #         "command": "npx",
            #         "args": [
            #             "mcp-remote@0.0.22",
            #             "https://mcp.coresignal.com/sse",
            #             "--header",
            #             "apikey:${AUTH_HEADER}"
            #         ],
            #         "env": {"AUTH_HEADER": self.coresignal_api_key}
            #     },
            #     cache_tools_list=True,
            #     client_session_timeout_seconds=1800,
            #     name="coresignal",
            # )
            mcp_server = MCPServerSse(
                    params={
                        "url": "https://mcp.coresignal.com/sse",
                        "headers": { "apikey": self.coresignal_api_key }
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
        # Parse the query for any specific number mentioned
        import re
        numbers_in_query = re.findall(r'\b(\d+)\b', search_request.query)
        
        if numbers_in_query:
            requested_count = int(numbers_in_query[0])
            target_count = min(requested_count, search_request.max_results)
            logger.info(f"Detected number '{requested_count}' in query, targeting {target_count} companies")
        else:
            requested_count = search_request.max_results
            target_count = search_request.max_results
            logger.info(f"No specific number in query, using max_results: {target_count}")
            
        return f"""
Using the system instructions provided earlier, complete the following task:\n
Query: "{search_request.query}"

Find {requested_count} companies matching this query: "{search_request.query}".

Only return the exact number of matching companies with their name and description. Stop after retrieving them. No retries, summaries, or commentary.
"""

    def _convert_to_search_response(self, 
                                  mcp_response: CoreSignalMCPResponse, 
                                  search_request: SearchRequest,
                                  total_tokens: int) -> SearchResponse:
        """Convert CoreSignalMCPResponse to SearchResponse format"""
        
        # Convert companies to simple name + description format
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
                "max_results": search_request.max_results,
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
                "max_results": search_request.max_results,
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

    def explain_query(self, query: str) -> Dict[str, Any]:
        """
        Explain what the agent would search for without executing.
        Useful for debugging and transparency.
        """
        return {
            "original_query": query,
            "processing_method": "agent_sdk_with_coresignal_mcp",
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "explanation": f"Will use Agent SDK with o3 model to interpret '{query}' and search Coresignal database via MCP",
            "expected_actions": [
                "Parse natural language query with high reasoning",
                "Identify search criteria (industry, location, size, etc.)",
                "Execute Coresignal MCP search commands", 
                "Return structured company list with names and descriptions"
            ]
        } 