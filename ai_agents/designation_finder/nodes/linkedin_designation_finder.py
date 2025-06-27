"""
LinkedIn Designation Finder Node
Searches LinkedIn for people with specific designations at companies
"""
from typing import Dict, Any, List
import orjson
from agents import Agent, Runner, ModelSettings
from agents.mcp.server import MCPServerStdio
from openai.types import Reasoning

from ai_agents.designation_finder.models import DesignationFinderState, LinkedInProfile


class LinkedInDesignationFinder:
    """
    LinkedIn-based designation finder using browserMCP
    Finds people with specific designations at companies (fuzzy matching)
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def search_designation_at_company(self, company_name: str, designation: str) -> List[LinkedInProfile]:
        """
        Search LinkedIn for people with a specific designation at a company
        Returns up to 5 profiles maximum with fuzzy matching
        """
        print(f"🔍 Searching for {designation} at {company_name}")

        browser_mcp = None
        profiles_found = []

        try:
            # Create MCP connection
            browser_mcp = MCPServerStdio(
                name="browsermcp",
                params={
                    "command": "npx",
                    "args": ["@browsermcp/mcp@latest"],
                    "env": {
                        "MCP_AGENT_TOOL_MAX_STEPS": "200",
                        "MCP_AGENT_TOOL_MAX_ACTIONS_PER_STEP": "50",
                    },
                },
                cache_tools_list=True,
                client_session_timeout_seconds=900
            )

            await browser_mcp.connect()

            # Build search prompt
            prompt = f"""Find multiple people at "{company_name}" whose current titles match or are similar to "{designation}" and give me the JSON result as specified."""

            # Set up agent
            agent = Agent(
                name="LinkedInDesignationSearchAgent",
                model="o3",
                model_settings=ModelSettings(
                    reasoning=Reasoning(effort="medium"),
                    extra_body={"service_tier": "flex"}
                ),
                mcp_servers=[browser_mcp],
                instructions=f"""You are a web-capable assistant.  
Task: visit LinkedIn and search for people who work at “{company_name}” with titles matching or similar to “{designation}”.  
Use fuzzy title matching, e.g.:

• CEO → Chief Executive Officer, Co-CEO, President & CEO, etc.  
• CTO → Chief Technology Officer, Chief Technical Officer, Co-CTO, etc.  
• VP Sales → Vice President Sales, VP of Sales, Sales VP, Director of Sales, etc.  
• Marketing Manager → Marketing Manager, Marketing Director, Head of Marketing, etc.  

Steps  
1. Go to linkedin.com and run the search “{designation}” AND “{company_name}”.  
2. Scan results for current titles that match (exactly or fuzzily) “{designation}”.  
3. For every suitable profile found (collect several, up to a reasonable limit such as 10):  
   • Full name  
   • Current job title  
   • Profile URL  

Output strictly as a JSON array, one object per profile, each with:

[
  {
    "name": "…",
    "title": "…",
    "linkedin_url": "…",
    "company_name": "{company_name}"
  },
  …
]

If none qualify, return `[]`. Respond with JSON only—no commentary.
"""
            )

            # Run the search
            result = await Runner.run(
                starting_agent=agent,
                input=prompt,
                max_turns=50
            )

            # Process the response
            response_text = str(result.final_output)
            profiles_found = self._parse_search_results(response_text, company_name, designation)

            print(f"✅ Found {len(profiles_found)} profiles for {designation} at {company_name}")

        except Exception as e:
            print(f"❌ LinkedIn search failed for {designation} at {company_name}: {str(e)}")

        finally:
            if browser_mcp:
                try:
                    await browser_mcp.cleanup()
                except Exception as cleanup_error:
                    print(f"⚠️ MCP cleanup error: {cleanup_error}")

        return profiles_found

    def _parse_search_results(self, response_text: str, company_name: str, designation: str) -> List[LinkedInProfile]:
        """Parse the AI response and extract LinkedIn profiles"""
        profiles = []

        try:
            # Try to extract JSON from the response
            response_text = response_text.strip()

            # Look for JSON in the response
            if response_text.startswith('[') and response_text.endswith(']'):
                data = orjson.loads(response_text)
            else:
                # Try to find JSON within the text
                import re
                json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if json_match:
                    data = orjson.loads(json_match.group())
                else:
                    print(f"⚠️ No valid JSON found in response for {company_name}")
                    return profiles

            # Convert to LinkedInProfile objects
            for item in data[:5]:  # Maximum 5 profiles
                if isinstance(item, dict):
                    name = item.get('name', '').strip()
                    title = item.get('title', '').strip()
                    linkedin_url = item.get('linkedin_url', '').strip()

                    if name and linkedin_url:
                        profile = LinkedInProfile(
                            name=name,
                            linkedin_url=linkedin_url,
                            title=title,
                            company_name=company_name,
                            designation_searched=designation
                        )
                        profiles.append(profile)

        except Exception as e:
            print(f"⚠️ Error parsing search results for {company_name}: {str(e)}")

        return profiles


async def linkedin_designation_finder(state: DesignationFinderState, config: Dict[str, Any] = None) -> DesignationFinderState | None:
    """
    LinkedIn designation finder node - single company processing
    """
    import asyncio

    print(f"🔍 [LINKEDIN_FINDER] Starting LinkedIn designation finder node")

    # Step 1: Validate input
    print(f"🔍 [LINKEDIN_FINDER] Step 1: Validating input state")
    if not state.current_company_designation:
        error_msg = "No company designation provided for processing"
        state.errors.append(error_msg)
        print(f"❌ [LINKEDIN_FINDER] {error_msg}")
        return state

    company_name = state.current_company_designation.company_name
    designation = state.current_company_designation.designation
    
    print(f"✅ [LINKEDIN_FINDER] Input validated")
    print(f"🏢 [LINKEDIN_FINDER] Company: {company_name}")
    print(f"👔 [LINKEDIN_FINDER] Designation: {designation}")

    print(f"🎯 [LINKEDIN_FINDER] Processing: {designation} at {company_name}")

    try:
        # Step 2: Prepare configuration
        print(f"⚙️ [LINKEDIN_FINDER] Step 2: Preparing configuration")
        config = config.get("configurable", {}) if config else {}
        print(f"✅ [LINKEDIN_FINDER] Configuration prepared")

        # Step 3: Initialize LinkedIn finder
        print(f"🚀 [LINKEDIN_FINDER] Step 3: Initializing LinkedIn finder")
        finder = LinkedInDesignationFinder(config)
        print(f"✅ [LINKEDIN_FINDER] LinkedIn finder initialized")

        # Step 4: Execute search
        print(f"🔍 [LINKEDIN_FINDER] Step 4: Executing LinkedIn search")
        print(f"🔎 [LINKEDIN_FINDER] Searching for '{designation}' at '{company_name}'...")
        
        profiles = await finder.search_designation_at_company(company_name, designation)
        
        print(f"✅ [LINKEDIN_FINDER] Search completed")
        print(f"📊 [LINKEDIN_FINDER] Search returned {len(profiles) if profiles else 0} profiles")

        # Step 5: Process and store results
        print(f"📝 [LINKEDIN_FINDER] Step 5: Processing search results")
        
        if profiles:
            print(f"✅ [LINKEDIN_FINDER] Found {len(profiles)} profiles - storing results")
            
            # Log each profile found
            for i, profile in enumerate(profiles, 1):
                print(f"   [LINKEDIN_FINDER] Profile {i}:")
                print(f"      - Name: {profile.name}")
                print(f"      - LinkedIn: {profile.linkedin_url}")
                print(f"      - Title: {profile.title or 'N/A'}")
                print(f"      - Company: {profile.company_name}")
                print(f"      - Searched for: {profile.designation_searched}")
            
            # Store in state
            state.found_profiles.extend(profiles)
            print(f"✅ [LINKEDIN_FINDER] Stored {len(profiles)} profiles in state")
            print(f"🎉 [LINKEDIN_FINDER] Successfully found {len(profiles)} profiles for {company_name}")
            
        else:
            print(f"⚠️ [LINKEDIN_FINDER] No profiles found for {designation} at {company_name}")
            print(f"📝 [LINKEDIN_FINDER] This will be logged as 'no results' in CSV")

        # Step 6: Final validation
        print(f"🔍 [LINKEDIN_FINDER] Step 6: Final state validation")
        total_profiles_in_state = len(state.found_profiles)
        print(f"📊 [LINKEDIN_FINDER] Total profiles now in state: {total_profiles_in_state}")
        
        print(f"✅ [LINKEDIN_FINDER] LinkedIn search processing completed successfully")

    except Exception as e:
        error_msg = f"Error processing {company_name}: {str(e)}"
        state.errors.append(error_msg)
        print(f"❌ [LINKEDIN_FINDER] ERROR: {error_msg}")
        print(f"🔍 [LINKEDIN_FINDER] Error details: {type(e).__name__}: {str(e)}")
        
        # Additional error context
        try:
            print(f"🔍 [LINKEDIN_FINDER] Error context:")
            print(f"   - Company: {company_name}")
            print(f"   - Designation: {designation}")
            print(f"   - Config available: {config is not None}")
            print(f"   - State valid: {state is not None}")
        except Exception as ctx_error:
            print(f"⚠️ [LINKEDIN_FINDER] Could not gather error context: {ctx_error}")

    print(f"🔚 [LINKEDIN_FINDER] LinkedIn finder node execution completed for {company_name}")
    return state