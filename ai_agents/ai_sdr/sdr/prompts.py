"""
Centralized Prompts Configuration

This file contains all system and user prompts used across the SDR workflow.
Users can customize these prompts or provide their own at runtime.
"""

import json
import os
from typing import Dict, Any
from ai_agents.ai_sdr.sdr.logging_config import clean_log, prompt_log


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

    "prospect_enricher_instructions": """You are a LinkedIn Research Specialist with full browser automation via **Browser MCP**.
Your sole task is to locate executive-level decision makers on LinkedIn and collect their
profile URLs.

Always issue navigation, click, and scroll actions through Browser MCP.
If the current URL is not on LinkedIn, send an MCP **navigate** command to https://www.linkedin.com
and wait for the page load event before continuing.

CRITICAL SCROLLING AND PAGINATION INSTRUCTIONS:
1. **Ensure LinkedIn Context**  
   • If `window.location.host !== "www.linkedin.com"`, MCP-navigate to LinkedIn home.  
2. **Search for the Company**  
   • MCP-type company name in the top search box → press Enter.  
   • MCP-switch to the **Companies** result tab.  
   • Click the result whose heading exactly matches `{{company_name}}`.  
3. **Open “People” > “See all people”**  
   • If “People” is hidden, scroll until it appears.  
   • Click “See all people”.  
4. **Filtering & Scrolling**  
   • Use keyword filter to include ONLY profiles whose headline matches any of  
     `{{target_executive_keywords}}` (case-insensitive).  
   • For each page:  
     – Scroll 600 px, wait 2 s.  
     – Click “Load more” if visible.  
     – Stop when “No more results” OR 50 profiles processed.  
5. **Profile Capture**  
   • For every matching profile:  
     – MCP-open in new tab, wait 3 s.  
     – Extract: Full Name, Headline, Profile URL.  
     – Close tab, return to list.  
6. **Error Handling & Logging**  
   • Log every MCP action (`navigate`, `click`, `type`, `scroll`).  
   • If a page fails to load after 10 s, record `"load_timeout"` and continue.

If the search is not successful, give the reason out. 

IMPORTANT: The response will be automatically formatted as structured data using the LinkedInProspectResponse model.
Ensure all required fields are properly populated:
- linkedin_research: Summary information about the search
- executives_found: List of executive profiles found
- all_profiles_found: List of all profiles discovered

Focus on accuracy and completeness of the LinkedIn profile URLs and contact information.""",

    "prospect_enricher_user_prompt": """COMPANY: {company_name}
WEBSITE: {company_website}
INDUSTRY: {industry}

TARGET EXECUTIVES TO FIND ONLY on LinkedIn are given below:
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
        "business_type": "online_grocer/offline_grocer/not_grocery/unclear",
        "key_factors": ["List of 2-3 key factors that influenced the relevance decision"]
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
    Get prompts from user input at the start of execution with enhanced functionality

    Returns:
        Dictionary of custom prompts provided by user
    """
    prompt_log("\n" + "=" * 80)
    prompt_log("🎯 ENHANCED PROMPT CUSTOMIZATION")
    prompt_log("=" * 80)
    prompt_log("You can customize the prompts used in the SDR workflow.")
    prompt_log("Each prompt can be viewed before customization and you can choose to:")
    prompt_log("• View the default prompt")
    prompt_log("• Use the default prompt")
    prompt_log("• Enter a custom prompt")
    prompt_log("• Skip prompt customization entirely")
    
    prompt_log("\nAvailable prompts to customize:")
    prompt_log("1. LinkedIn Research Instructions - Controls how LinkedIn profiles are searched")
    prompt_log("2. Web Research System Prompt - Controls how companies are analyzed for relevance")
    prompt_log("3. HubSpot Contact Creation - Controls how contacts are created in HubSpot")
    prompt_log("4. User Prompt Templates - Controls user-facing prompt templates")
    prompt_log("5. Target Executives List - Controls which roles to search for on LinkedIn")
    prompt_log("6. Customize All Prompts - Interactive customization of all prompts")
    prompt_log("7. View All Defaults - Display all default prompts without customizing")
    prompt_log("8. Skip - Use all default prompts")

    choice = input("\nEnter your choice (1-8) or press Enter to skip: ").strip()
    if not choice:
        choice = "8"

    custom_prompts = {}

    if choice == "1":
        custom_prompts.update(_customize_single_prompt(
            "prospect_enricher_instructions",
            "LinkedIn Research Instructions",
            "Controls how the AI searches for and collects LinkedIn profiles of company executives"
        ))

    elif choice == "2":
        custom_prompts.update(_customize_single_prompt(
            "web_enricher_system_prompt",
            "Web Research System Prompt",
            "Controls how the AI analyzes companies for business relevance and gathers information"
        ))

    elif choice == "3":
        custom_prompts.update(_customize_single_prompt(
            "hubspot_creator_instructions",
            "HubSpot Contact Creation Instructions",
            "Controls how LinkedIn profiles are converted into HubSpot contacts"
        ))

    elif choice == "4":
        prompt_log("\n📝 Customizing User Prompt Templates:")
        user_prompts = [
            ("prospect_enricher_user_prompt", "LinkedIn User Prompt Template"),
            ("web_enricher_user_prompt", "Web Research User Prompt"),
            ("hubspot_creator_user_prompt", "HubSpot User Prompt Template")
        ]
        for key, name in user_prompts:
            custom_prompts.update(_customize_single_prompt(key, name, f"Template used for {name.lower()}"))

    elif choice == "5":
        custom_prompts.update(_customize_single_prompt(
            "prospect_enricher_target_executives",
            "Target Executives List",
            "Defines which executive roles to search for on LinkedIn (comma-separated list)"
        ))

    elif choice == "6":
        prompt_log("\n📝 Interactive Customization of All Prompts:")
        all_prompts = [
            ("prospect_enricher_instructions", "LinkedIn Research Instructions"),
            ("prospect_enricher_user_prompt", "LinkedIn User Prompt Template"),
            ("web_enricher_system_prompt", "Web Research System Prompt"),
            ("web_enricher_user_prompt", "Web Research User Prompt"),
            ("hubspot_creator_instructions", "HubSpot Contact Creation Instructions"),
            ("hubspot_creator_user_prompt", "HubSpot User Prompt Template"),
            ("prospect_enricher_target_executives", "Target Executives List")
        ]
        
        for key, name in all_prompts:
            custom_prompts.update(_customize_single_prompt(key, name, f"Customize {name.lower()}"))

    elif choice == "7":
        _display_all_default_prompts()
        return {}

    elif choice == "8":
        prompt_log("\n✅ Using all default prompts")
        return {}

    else:
        prompt_log("\n⚠️ Invalid choice, using default prompts")
        return {}

    if custom_prompts:
        prompt_log(f"\n✅ Using {len(custom_prompts)} custom prompt(s)")
        _show_customization_summary(custom_prompts)
    else:
        prompt_log("\n✅ Using default prompts")

    return custom_prompts


def _customize_single_prompt(prompt_key: str, prompt_name: str, description: str) -> Dict[str, str]:
    """
    Customize a single prompt with enhanced options
    
    Args:
        prompt_key: Key for the prompt in DEFAULT_PROMPTS
        prompt_name: Human-readable name for the prompt
        description: Description of what this prompt controls
    
    Returns:
        Dictionary with custom prompt if provided, empty dict otherwise
    """
    prompt_log(f"\n" + "─" * 60)
    prompt_log(f"📝 Customizing: {prompt_name}")
    prompt_log("─" * 60)
    prompt_log(f"Description: {description}")
    
    default_prompt = DEFAULT_PROMPTS.get(prompt_key, "No default available")
    
    prompt_log("\nWhat would you like to do?")
    prompt_log("1. View default prompt")
    prompt_log("2. Use default prompt (no changes)")
    prompt_log("3. Enter custom prompt")
    prompt_log("4. Skip this prompt")
    
    sub_choice = input("Enter your choice (1-4): ").strip()
    
    if sub_choice == "1":
        _display_prompt_with_formatting(prompt_name, default_prompt)
        
        # After viewing, ask what to do next
        prompt_log("\nAfter viewing the default, what would you like to do?")
        prompt_log("1. Use this default prompt")
        prompt_log("2. Enter a custom prompt")
        prompt_log("3. Skip this prompt")
        
        follow_up = input("Enter your choice (1-3): ").strip()
        
        if follow_up == "2":
            return _get_custom_prompt_input(prompt_key, prompt_name)
        elif follow_up == "1":
            prompt_log(f"✅ Using default prompt for {prompt_name}")
            return {}
        else:
            prompt_log(f"⏭️ Skipping {prompt_name}")
            return {}
    
    elif sub_choice == "2":
        prompt_log(f"✅ Using default prompt for {prompt_name}")
        return {}
    
    elif sub_choice == "3":
        return _get_custom_prompt_input(prompt_key, prompt_name)
    
    else:
        prompt_log(f"⏭️ Skipping {prompt_name}")
        return {}


def _get_custom_prompt_input(prompt_key: str, prompt_name: str) -> Dict[str, str]:
    """
    Get custom prompt input from user with multi-line support
    
    Args:
        prompt_key: Key for the prompt
        prompt_name: Human-readable name
    
    Returns:
        Dictionary with custom prompt
    """
    prompt_log(f"\n✏️ Enter custom prompt for {prompt_name}")
    prompt_log("💡 Tips:")
    prompt_log("   • Press Enter twice to finish")
    prompt_log("   • Use clear, specific instructions")
    prompt_log("   • Include formatting requirements if needed")
    prompt_log("   • Type 'DEFAULT' to use the default prompt")
    prompt_log("\nEnter your custom prompt (press Enter twice when done):")
    
    lines = []
    empty_line_count = 0
    
    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_line_count += 1
                if empty_line_count >= 2:
                    break
                lines.append(line)
            else:
                empty_line_count = 0
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    custom_prompt = "\n".join(lines).strip()
    
    if not custom_prompt or custom_prompt.upper() == "DEFAULT":
        prompt_log(f"✅ Using default prompt for {prompt_name}")
        return {}
    
    prompt_log(f"✅ Custom prompt set for {prompt_name} ({len(custom_prompt)} characters)")
    return {prompt_key: custom_prompt}


def _display_prompt_with_formatting(prompt_name: str, prompt_content: str):
    """
    Display a prompt with nice formatting
    
    Args:
        prompt_name: Name of the prompt
        prompt_content: Content to display
    """
    prompt_log(f"\n" + "═" * 80)
    prompt_log(f"📋 DEFAULT PROMPT: {prompt_name}")
    prompt_log("═" * 80)
    
    # Truncate very long prompts for readability
    if len(prompt_content) > 2000:
        truncated = prompt_content[:2000] + "\n\n[... content truncated for display ...]"
        prompt_log(truncated)
        prompt_log(f"\n📊 Full prompt length: {len(prompt_content)} characters")
    else:
        prompt_log(prompt_content)
    
    prompt_log("═" * 80)


def _display_all_default_prompts():
    """Display all default prompts for reference"""
    prompt_log("\n" + "═" * 80)
    prompt_log("📚 ALL DEFAULT PROMPTS REFERENCE")
    prompt_log("═" * 80)
    
    prompt_categories = {
        "LinkedIn Research Prompts": [
            ("prospect_enricher_instructions", "LinkedIn Research Instructions"),
            ("prospect_enricher_user_prompt", "LinkedIn User Prompt Template"),
            ("prospect_enricher_retry_prompt", "LinkedIn Retry Prompt"),
            ("prospect_enricher_target_executives", "Target Executives List")
        ],
        "Web Research Prompts": [
            ("web_enricher_system_prompt", "Web Research System Prompt"),
            ("web_enricher_user_prompt", "Web Research User Prompt"),
            ("web_enricher_output_format", "Web Research Output Format")
        ],
        "HubSpot Integration Prompts": [
            ("hubspot_creator_instructions", "HubSpot Contact Creation Instructions"),
            ("hubspot_creator_user_prompt", "HubSpot User Prompt Template"),
            ("hubspot_creator_retry_prompt", "HubSpot Retry Prompt")
        ]
    }
    
    for category, prompts in prompt_categories.items():
        prompt_log(f"\n🏷️ {category}")
        prompt_log("─" * 60)
        
        for key, name in prompts:
            prompt_content = DEFAULT_PROMPTS.get(key, "No default available")
            prompt_log(f"\n📝 {name} ({key}):")
            
            # Show first 200 characters of each prompt
            if len(prompt_content) > 200:
                preview = prompt_content[:200] + "..."
            else:
                preview = prompt_content
            
            prompt_log(f"   {preview}")
            prompt_log(f"   📊 Length: {len(prompt_content)} characters")
    
    prompt_log("\n" + "═" * 80)
    prompt_log("💡 Use option 6 to customize any of these prompts interactively")
    prompt_log("═" * 80)


def _show_customization_summary(custom_prompts: Dict[str, str]):
    """
    Show summary of customized prompts
    
    Args:
        custom_prompts: Dictionary of custom prompts
    """
    prompt_log("\n" + "─" * 60)
    prompt_log("📋 CUSTOMIZATION SUMMARY")
    prompt_log("─" * 60)
    
    for key, value in custom_prompts.items():
        # Convert key to readable name
        readable_name = key.replace("_", " ").title()
        prompt_log(f"✏️ {readable_name}: {len(value)} characters")
    
    prompt_log("─" * 60)


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
        clean_log(f"Prompts file not found: {file_path}", level="warning")
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            custom_prompts = json.load(f)
        clean_log(f"Loaded {len(custom_prompts)} custom prompts from {file_path}")
        return custom_prompts
    except Exception as e:
        clean_log(f"Error loading prompts file: {e}", level="error")
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
        clean_log(f"Saved custom prompts to {file_path}")
    except Exception as e:
        clean_log(f"Error saving prompts file: {e}", level="error")
