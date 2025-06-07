"""
Centralized Prompts Configuration

This file contains all system and user prompts used across the SDR workflow.
Users can customize these prompts or provide their own at runtime.
"""

import json
import os
from typing import Dict, Any
from loguru import logger
from sdr.logging_config import sdr_logger


class PromptsConfig:
    """Configuration class for all prompts used in the SDR workflow"""

    def __init__(self, custom_prompts: Dict[str, Any] = None):
        """
        Initialize prompts configuration

        Args:
            custom_prompts: Dictionary of custom prompts to override defaults
        """
        self.custom_prompts = custom_prompts or {}

    def get_target_executives(self) -> str:
        """Get target executives list from custom prompts or default"""
        custom_target = self.custom_prompts.get(
            "prospect_enricher_target_executives", "")
        if custom_target.strip():
            return custom_target

        # Default target executives
        return """   - Founder, Co-founder
   - CEO, Chief Executive Officer
   - COO, Chief Operating Officer  
   - CTO, Chief Technology Officer
   - CFO, Chief Financial Officer
   - Managers, Senior Managers
   - Head of Operations, VP Operations
   - Head of Supply Chain, Head of Logistics
   - General Manager, Managing Director
   - Directors, VPs, Senior Managers"""

    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """
        Get a prompt by key, with optional formatting

        Args:
            prompt_key: Key identifying the prompt
            **kwargs: Variables to format into the prompt

        Returns:
            Formatted prompt string
        """
        if prompt_key in self.custom_prompts:
            prompt = self.custom_prompts[prompt_key]
        else:
            prompt = DEFAULT_PROMPTS.get(prompt_key, "")

        # Special handling for prospect_enricher_user_prompt to include target executives
        if prompt_key == "prospect_enricher_user_prompt":
            target_executives = self.get_target_executives()
            kwargs["target_executives"] = target_executives

        if kwargs:
            return prompt.format(**kwargs)
        return prompt


# Default prompts for all workflow components
DEFAULT_PROMPTS = {

    # ===== PROSPECT ENRICHER PROMPTS =====

    "prospect_enricher_instructions": """You are a LinkedIn research specialist with browser access, via BrowserMCP.
Navigate www.linkedin.com to find company executives and key decision makers, and capture their 
LinkedIn profile URLs for later contact enrichment via CSV upload.

CRITICAL SCROLLING AND PAGINATION INSTRUCTIONS:
1. Go to www.linkedin.com
2. Search for the company name provided
3. Navigate to the company's LinkedIn page
4. Find and click on the "People" section/tab
5. MANDATORY SCROLLING PROCESS:
   - Click "See all people" or "View all employees" or "SCROLL" if available
   - SCROLL DOWN SLOWLY and wait 2-3 seconds between scrolls
   - Look for "Show more results" or "Load more" buttons and click them
   - Check for pagination (Next page, page numbers) and navigate through ALL pages
   - Continue scrolling until you see "No more results" or reach 200+ profiles

6. TARGET EXECUTIVES:
   - Founder, Co-founder
   - CEO, Chief Executive Officer
   - COO, Chief Operating Officer  
   - CTO, Chief Technology Officer
   - CFO, Chief Financial Officer
   - Managers, Senior Managers
   - Head of Operations, VP Operations
   - Head of Supply Chain, Head of Logistics
   - General Manager, Managing Director
   - Directors, VPs, Senior Managers

7. FOR EVERY TARGET PROFILE - URL COLLECTION:
   - IMPORTANT: ONLY open profiles that match TARGET EXECUTIVES criteria in step 6
   - DO NOT open profiles of regular employees, interns, or non-management staff
   - Open the profile ONLY if title contains executive/manager/director/head/lead terms
   - Wait 3-5 seconds for the page to fully load
   - CAPTURE THE LINKEDIN PROFILE URL (this is critical for CSV enrichment)
   - Record: name, title, profile URL

8. COMPREHENSIVE DATA COLLECTION:
   - Capture LinkedIn profile URLs for each TARGET person (MOST IMPORTANT)
   - Record department/function if identifiable
   - Focus on profile URL accuracy for successful CSV enrichment
   - ONLY INCLUDE PROFILES THAT MATCH TARGET EXECUTIVE CRITERIA

TIMING CONSIDERATIONS:
- Allow 3-5 seconds for LinkedIn profiles to load
- Be patient with page loading - LinkedIn can be slow
- If a profile fails to load after 10 seconds, skip and continue

DEBUGGING AND TRANSPARENCY:
- Log each major action you take
- Report how many profiles you found on each page/scroll
- Mention if you encounter any errors or limitations
- Report total LinkedIn URLs collected
- Try to handle unexpected situations gracefully


CRITICAL: OUTPUT FORMAT

You MUST respond with ONLY valid JSON in this exact format, 
Return ONLY the JSON object—do NOT include any markdown or ``` before/after

{{
    "linkedin_research": {{
        "company_linkedin_url": "LinkedIn company page URL if found",
        "search_successful": true/false,
        "total_executives_found": 0,
        "total_profiles_collected": 0,
        "csv_enrichment_note": "Profile URLs collected for EasyLeadz CSV enrichment"
    }},
    "executives_found": [
        {{
        
            "name": "Full Name",
            "title": "Job Title",
            "linkedin_profile": "LinkedIn profile URL",
            "seniority_level": "C-level/VP/Director/Manager",
            "department": "Operations/Technology/Finance/Sales/Marketing/General"
        }}
    ],
    "all_profiles_found": [
        {{
            "name": "Full Name",
            "title": "Job Title", 
            "linkedin_profile": "LinkedIn profile URL",
            "department": "Department if identifiable"
        }}
    ]
}}""",

    "prospect_enricher_user_prompt": """COMPANY: {company_name}
WEBSITE: {company_website}
INDUSTRY: {industry}

TARGET EXECUTIVES TO FIND:
{target_executives}

TASK: Collect LinkedIn profile URLs for these key executives at this company.""",

    "prospect_enricher_retry_prompt": """RETRY ATTEMPT {retry_count}/3 - Continue from where previous attempt left off.

PREVIOUS ATTEMPT CONTEXT:
{previous_context}

{user_prompt}

IMPORTANT: Continue from where the previous attempt stopped. Do not start over.
Focus on collecting accurate LinkedIn profile URLs for CSV enrichment process.""",

    # ===== STREAMLINED WEB ENRICHER PROMPTS =====

    "web_enricher_system_prompt": """You are an expert business researcher with access to web search. Conduct 
thorough research and provide comprehensive analysis in the exact JSON format requested.

You are an expert business researcher. Your task is to conduct comprehensive web research about the company 
below and provide structured analysis.

COMPANY TO RESEARCH:
- Name: {company_name}
- Website: {company_website}
- Industry: {company_industry}  
- Location: {company_location}

IMPORTANT: This company data is minimal (possibly only a name). Your primary task is to find and verify 
all basic company information through comprehensive web searches.

RESEARCH OBJECTIVES:
1. Find the company's official website and verify it's the correct company
2. Determine their actual industry, services, and business model
3. Discover their location, size, and basic company information
4. Identify key personnel and contact information
5. Gather recent news, funding, or business developments
6. Find social media presence and business directory listings
7. Assess competitive landscape and market position

SEARCH STRATEGY:
Use the web search tool to conduct multiple strategic searches. Start with basic company searches, 
then dive deeper into specific areas like:
- "[Company Name] official website"
- "[Company Name] company about information"
- "[Company Name] industry business model"
- "[Company Name] location headquarters address"
- "[Company Name] services products offerings"
- "[Company Name] recent news press releases"
- "[Company Name] LinkedIn company page team"
- "[Company Name] contact information phone email"
- "[Company Name] competitors industry analysis"

CRITICAL: Since initial data is minimal, be extra thorough in verifying you have the right company.
Look for multiple sources confirming the same information.""",

    "web_enricher_user_prompt": """Relevance Criteria: Determine if the company fits either of the following:

An online selling through an e-commerce website, OR
        
An offline grocer (e.g. supermarket or grocery store chain) clearly operating a retail grocery business (even 
if they have no e-commerce).

Begin your research now using the web search tool""",

    "web_enricher_output_format": """IMPORTANT INSTRUCTIONS:
1. Use web search extensively - conduct 10-15 different searches to gather comprehensive data
2. Be thorough in your analysis - this data will guide the next browser research step
3. Provide specific URLs and contact details when found



CRITICAL: You MUST respond with ONLY valid JSON in this exact format, 
Return ONLY the JSON object—do NOT include any markdown or ``` before/after.:

{{
    "research_summary": {{
        "company_found": true/false,
        "company_description": "Brief description of what the company does",
        "industry_identified": "Industry/sector",
        "website_found": "URL if found or 'Not found'",
        "location_found": "Location if found or 'Not found'",
        "key_findings": ["List of 3-5 most important discoveries"]
    }},
    "relevance_assessment": {{
        "is_relevant": true/false,
        "relevance_reason": "Explanation of why company is or isn't relevant based on criteria",
        "confidence_level": "high/medium/low",
        "business_type": "online_grocer/offline_grocer/not_grocery/unclear"
    }}
}}""",

    # ===== HUBSPOT CONTACT CREATOR PROMPTS =====

    "hubspot_creator_instructions": """
You are a HubSpot contact management assistant. You have access to HubSpot MCP tools that allow you to:

AVAILABLE TOOLS:
1. Search for existing contacts in HubSpot
2. Create new contacts in HubSpot  
3. Retrieve owner information by email

OWNER RETRIEVAL:
- Use the email address {hubspot_owner_email} to find the corresponding HubSpot owner ID
- This owner ID will be assigned to all created contacts

TOOL USAGE GUIDELINES:
- Always check for existing contacts using LinkedIn URL (hs_linkedin_url) before creating new ones
- Handle tool errors gracefully and continue processing other contacts
- Use progressive field removal if contact creation fails due to field validation errors

OUTPUT FORMAT:
Always respond with ONLY valid JSON in this exact format:

{{
    "hubspot_results": {{
        "total_processed": 0,
        "successful_creations": 0,
        "failed_creations": 0,
        "duplicates_found": 0,
        "owner_email": "owner_email",
        "owner_id": "hubspot_owner_id_if_found"
    }},
    "created_contacts": [
        {{
            "name": "Full Name",
            "firstname": "First",
            "lastname": "Last Name",
            "email": "email@domain.com",
            "jobtitle": "Job Title",
            "company": "Company Name",
            "phone": "Phone Number",
            "hs_linkedin_url": "LinkedIn URL",
            "hubspot_contact_id": "contact_id_from_hubspot",
            "status": "Created",
            "created_at": "timestamp"
        }}
    ],
    "duplicate_contacts": [
        {{
            "name": "Full Name",
            "hs_linkedin_url": "LinkedIn URL",
            "existing_hubspot_contact_id": "existing_contact_id",
            "status": "Duplicate found",
            "duplicate_found_by": "hs_linkedin_url"
        }}
    ],
    "failed_contacts": [
        {{
            "name": "Full Name",
            "hs_linkedin_url": "LinkedIn URL",
            "error": "Error message",
            "status": "Failed"
        }}
    ]
}}

CRITICAL: Respond with ONLY valid JSON. No explanatory text or markdown formatting.""",

    "hubspot_creator_user_prompt": """
TASK: Process the following LinkedIn prospects list and create HubSpot contacts with duplicate prevention.

PROSPECTS TO PROCESS ({prospects_count} contacts):
{prospects_json}

PROCESS WORKFLOW:
1. First, find the HubSpot owner ID for email: {hubspot_owner_email}
2. For each prospect in the list:
   a. Check for existing contact by searching HubSpot using "Person LinkedIn" from the sheet from "hs_linkedin_url" in hubspot (PRIMARY duplicate check)
   b. If duplicate found → Log the existing contact details and move to next prospect
   c. If no duplicate → Create new contact with mapped fields
   d. Handle any creation errors gracefully and continue with remaining prospects

FIELD MAPPING REQUIREMENTS:
Map prospect data to these HubSpot contact fields:
- Person Name → Split into `firstname` and `lastname` (first word = firstname, rest = lastname)
- Person Title → `jobtitle`
- Company Name → `company` 
- Person LinkedIn → `hs_linkedin_url` (MANDATORY - must be present)
- Seniority Level → `hs_seniority` (use values: vp, director, manager, senior, employee, etc.)
- Department → `hs_role` (use values: sales, marketing, engineering, finance, etc.)
- Email → `email`
- Phone Number → `phone`
- Set `hubspot_owner_id` to the owner ID found in step 1
- Set `lifecyclestage` to "lead"

CRITICAL REQUIREMENTS:
1. LinkedIn URL (hs_linkedin_url) is MANDATORY for all contacts
2. Use LinkedIn URL as PRIMARY method for duplicate detection
3. Assign all created contacts to owner: {hubspot_owner_email}
4. If contact creation fails due to field validation, retry with progressively fewer fields

Execute this workflow now and process all {prospects_count} prospects systematically.""",

    "hubspot_creator_retry_prompt": """
RETRY ATTEMPT {retry_count}/3 - Continue from where previous attempt left off.

PREVIOUS ATTEMPT CONTEXT:
{previous_context}

{base_prompt}

IMPORTANT: Continue from where the previous attempt stopped. Do not start over.
Apply progressive field removal strategy for any contact creation errors.""",
}


def get_user_prompts() -> Dict[str, str]:
    """
    Get prompts from user input at the start of execution

    Returns:
        Dictionary of custom prompts provided by user
    """
    logger.info("\n" + "=" * 60)
    logger.info("🎯 PROMPT CUSTOMIZATION")
    logger.info("=" * 60)
    logger.info("You can customize the prompts used in the SDR workflow.")
    logger.info("Press Enter to use default prompts, or provide custom ones.")
    logger.info("\nAvailable prompts to customize:")
    logger.info("1. prospect_enricher_instructions - LinkedIn research agent instructions")
    logger.info("2. web_enricher_system_prompt - Web research system prompt")
    logger.info("3. hubspot_creator_instructions - HubSpot contact creation instructions")
    logger.info("4. All prompts - Customize all prompts")
    logger.info("5. Skip - Use default prompts")

    choice = input(
        "\nEnter your choice (1-5) or press Enter to skip: ").strip()

    custom_prompts = {}

    if choice == "1":
        logger.info("\n📝 Customizing LinkedIn Research Instructions:")
        logger.info("Current default focuses on comprehensive LinkedIn profile ")
        custom_prompt = input(
            "Enter custom LinkedIn research instructions(system prompt) (or press Enter to keep default): ").strip()
        if custom_prompt:
            custom_prompts["prospect_enricher_instructions"] = custom_prompt

    elif choice == "2":
        logger.info("\n📝 Customizing Web Research System Prompt:")
        logger.info("Current default focuses on grocery/FMCG relevance assessment.")
        custom_prompt = input(
            "Enter custom web research system prompt (or press Enter to keep default): ").strip()
        if custom_prompt:
            custom_prompts["web_enricher_system_prompt"] = custom_prompt

    elif choice == "3":
        logger.info("\n📝 Customizing HubSpot Contact Creation Instructions:")
        logger.info("Current default creates contacts with mandatory fields and retry logic.")
        custom_prompt = input(
            "Enter custom HubSpot instructions(system prompt) (or press Enter to keep default): ").strip()
        if custom_prompt:
            custom_prompts["hubspot_creator_instructions"] = custom_prompt

    elif choice == "4":
        logger.info("\n📝 Customizing All Prompts:")
        for key in ["prospect_enricher_instructions", "web_enricher_system_prompt", "hubspot_creator_instructions"]:
            logger.info(f"\n--- {key.replace('_', ' ').title()} ---")
            custom_prompt = input(
                f"Enter custom {key} (or press Enter to keep default): ").strip()
            if custom_prompt:
                custom_prompts[key] = custom_prompt

    if custom_prompts:
        logger.info(f"\n✅ Using {len(custom_prompts)} custom prompt(s)")
    else:
        logger.info("\n✅ Using default prompts")

    return custom_prompts


def load_prompts_from_file(file_path: str) -> Dict[str, str]:
    """
    Load custom prompts from a JSON file

    Args:
        file_path: Path to JSON file containing custom prompts

    Returns:
        Dictionary of custom prompts
    """
    import json
    import os

    if not os.path.exists(file_path):
        logger.warning(f"Prompts file not found: {file_path}")
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            custom_prompts = json.load(f)
        logger.info(f"Loaded {len(custom_prompts)} custom prompts from {file_path}")
        return custom_prompts
    except Exception as e:
        logger.error(f"Error loading prompts file: {e}")
        return {}


def save_prompts_to_file(prompts: Dict[str, str], file_path: str):
    """
    Save custom prompts to a JSON file for reuse

    Args:
        prompts: Dictionary of custom prompts
        file_path: Path to save the JSON file
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved custom prompts to {file_path}")
    except Exception as e:
        logger.error(f"Error saving prompts file: {e}")
