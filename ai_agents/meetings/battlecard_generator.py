"""Battlecard Generation Service for meeting preparation."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI

from config.loaded_config import loaded_config
from ai_agents.meetings.models import (
    Battlecard,
    BattlecardSection,
)
from ai_agents.meetings.deep_research_service import DeepResearchService
from ai_agents.meetings.product_knowledge_service import ProductKnowledgeService

logger = logging.getLogger(__name__)


BATTLECARD_SYSTEM_PROMPT = """You are a sales strategist helping prepare for an important client meeting. Generate a comprehensive battlecard that will help the sales rep have a successful conversation.

Based on the company research, contact information, products to discuss, and previous meeting history, create a battlecard with:

1. Company Snapshot - Key facts: what they do, size, geography, recent news, key initiatives
2. Contact Snapshot - Persona analysis: priorities, pain points, likely objections based on role
3. Why Now + Product Fit - Why this is the right time, which products solve their problems
4. Talking Points - 5-7 tailored bullets for the conversation
5. Likely Objections & Responses - Anticipate 3-5 objections with suggested responses
6. Discovery Questions - 5-7 role-based and qualification questions
7. Proof Points - Relevant case studies, metrics, success stories
8. Recommended Agenda - Suggested meeting structure with time breakdown
9. Key Risks - Potential deal blockers to watch for
10. Suggested Next Steps - Options for moving the deal forward

Return a JSON object with this structure:
{
  "company_snapshot": {
    "title": "Company Overview",
    "content": "summary paragraph",
    "bullet_points": ["key fact 1", "key fact 2"]
  },
  "contact_snapshot": {
    "title": "Contact Profile",
    "content": "persona analysis",
    "bullet_points": ["priority 1", "pain point 1"]
  },
  "why_now_product_fit": {
    "title": "Why Now & Product Fit",
    "content": "timing and fit analysis",
    "bullet_points": ["reason 1", "fit point 1"]
  },
  "talking_points": ["point 1", "point 2", ...],
  "likely_objections": [
    {"objection": "objection text", "response": "suggested response"}
  ],
  "discovery_questions": ["question 1", "question 2", ...],
  "proof_points": ["case study 1", "metric 1", ...],
  "recommended_agenda": "suggested agenda with timing",
  "key_risks": ["risk 1", "risk 2"],
  "suggested_next_steps": ["demo", "pilot", "technical evaluation", ...]
}
"""


# Product information for context
PRODUCT_INFO = {
    "GaaS": {
        "name": "Fynd Platform (GaaS)",
        "description": "Complete e-commerce platform for enterprise brands",
        "key_features": ["Headless commerce", "Multi-channel selling", "Real-time inventory"],
        "differentiators": ["Built for Indian market", "Faster implementation", "Integrated ecosystem"],
        "common_objections": {
            "integration": "Pre-built connectors for 50+ platforms",
            "cost": "Pay-as-you-grow model, ROI in 3-6 months",
        },
    },
    "OMS": {
        "name": "Fynd OMS",
        "description": "Omnichannel order management and fulfillment",
        "key_features": ["Real-time inventory sync", "Split shipping", "Returns management"],
        "differentiators": ["Native integration with logistics", "AI-powered allocation"],
        "common_objections": {
            "complexity": "Simplified setup with guided onboarding",
            "existing_systems": "Works alongside existing ERP/WMS",
        },
    },
    "WMS": {
        "name": "Fynd WMS",
        "description": "AI-powered warehouse management system",
        "key_features": ["Pick path optimization", "Real-time tracking", "Labor management"],
        "differentiators": ["Mobile-first", "Quick deployment", "AI recommendations"],
        "common_objections": {
            "hardware": "Works with existing scanners and devices",
            "training": "Intuitive UI, minimal training needed",
        },
    },
    "Storefront": {
        "name": "Fynd Storefront",
        "description": "Headless commerce storefront builder",
        "key_features": ["No-code builder", "Mobile optimization", "SEO built-in"],
        "differentiators": ["Lightning fast", "Customizable themes", "Integrated checkout"],
        "common_objections": {
            "customization": "Full flexibility with headless architecture",
            "migration": "Zero-downtime migration support",
        },
    },
    "StoreOS": {
        "name": "Fynd StoreOS",
        "description": "Point-of-sale and retail store management",
        "key_features": ["Unified inventory", "Endless aisle", "Staff management"],
        "differentiators": ["Offline capability", "Quick training", "Integrated payments"],
        "common_objections": {
            "hardware": "Works on any Android device",
            "downtime": "Offline mode ensures no sales lost",
        },
    },
}


class BattlecardGenerator:
    """
    Generator for pre-meeting battlecards.
    
    Creates comprehensive meeting preparation materials based on:
    - Company masterdata and deep research
    - Contact information and persona
    - Product context
    - Previous meeting history
    """
    
    def __init__(self):
        """Initialize the battlecard generator."""
        api_key = loaded_config.openai_api_key
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables. Battlecard generation will fail.")
        self._openai_client = AsyncOpenAI(api_key=api_key) if api_key else None
        self._deep_research_service = DeepResearchService()
        self._product_knowledge_service = ProductKnowledgeService()
    
    def _get_product_context(self, product_ids: List[str]) -> str:
        """Build product context from product IDs using ProductKnowledgeService."""
        if not product_ids:
            return "No specific products selected"
        
        # Get product info from knowledge service
        products_dict = self._product_knowledge_service.get_products_by_ids(product_ids)
        
        # Fallback to old PRODUCT_INFO if not in knowledge service
        for pid in product_ids:
            if pid not in products_dict and pid in PRODUCT_INFO:
                products_dict[pid] = PRODUCT_INFO[pid]
        
        if not products_dict:
            return "No product information available"
        
        # Use product knowledge service to format for AI
        return self._product_knowledge_service.get_product_context_for_ai(
            list(products_dict.keys()),
            include_competitors=True
        )
    
    def _format_company_research(self, company_data: Dict[str, Any], deep_research: Optional[Dict[str, Any]] = None) -> str:
        """Format company research data, prioritizing deep research if available."""
        if not company_data:
            return "No company data available"
        
        parts = [
            f"Company: {company_data.get('name', 'Unknown')}",
            f"Domain: {company_data.get('domain', 'N/A')}",
            f"Industry: {company_data.get('industry', 'N/A')}",
        ]
        
        # Use deep research if available (more recent and comprehensive)
        if deep_research:
            data = deep_research.get('data', {}) if isinstance(deep_research, dict) and 'data' in deep_research else deep_research
            
            if data.get('company_overview'):
                parts.append(f"\nCompany Overview: {data['company_overview']}")
            
            if data.get('recent_news'):
                parts.append("\nRecent News & Signals:")
                for news in data['recent_news'][:5]:  # Top 5
                    parts.append(f"- {news.get('title', 'N/A')} ({news.get('date', 'N/A')})")
                    parts.append(f"  Implication: {news.get('implication', 'N/A')}")
            
            if data.get('key_initiatives'):
                parts.append(f"\nKey Initiatives: {', '.join(data['key_initiatives'])}")
            
            if data.get('inferred_pain_points'):
                parts.append(f"\nInferred Pain Points: {', '.join(data['inferred_pain_points'])}")
            
            if data.get('tech_stack'):
                parts.append(f"\nTech Stack: {', '.join(data['tech_stack'])}")
        else:
            # Fallback to enriched data if deep research not available
            enriched = company_data.get('enriched_data', {})
            if enriched:
                web_analysis = enriched.get('web_search_analysis', {})
                if web_analysis:
                    summary = web_analysis.get('research_summary', {})
                    if summary:
                        parts.append(f"\nResearch Summary: {json.dumps(summary, indent=2)}")
        
        return "\n".join(parts)
    
    def _format_contact_info(self, contact_data: Dict[str, Any]) -> str:
        """Format contact information."""
        if not contact_data:
            return "No contact information available"
        
        name = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip()
        title = contact_data.get('job_title', 'N/A')
        
        parts = [
            f"Name: {name}",
            f"Title: {title}",
        ]
        
        if contact_data.get('email'):
            parts.append(f"Email: {contact_data['email']}")
        
        if contact_data.get('linkedin_url'):
            parts.append(f"LinkedIn: {contact_data['linkedin_url']}")
        
        return "\n".join(parts)
    
    def _format_previous_meetings(self, meetings: List[Dict[str, Any]]) -> str:
        """Format previous meeting history."""
        if not meetings:
            return "No previous meetings with this company/contact"
        
        parts = []
        for m in meetings[:5]:  # Last 5 meetings
            date = m.get('ended_at') or m.get('scheduled_at') or m.get('created_at')
            if date:
                date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else str(date)[:10]
            else:
                date_str = "Unknown"
            
            summary = m.get('summary', 'No summary')
            products = m.get('products_discussed', [])
            objections = m.get('objections_resolutions', [])
            next_steps = m.get('next_steps', [])
            
            meeting_info = f"""
**Meeting on {date_str}**
Summary: {summary[:300] if summary else 'N/A'}
Products Discussed: {', '.join(products) if products else 'N/A'}
Objections Raised: {', '.join([o.get('objection', '') for o in objections]) if objections else 'None'}
Next Steps Agreed: {', '.join(next_steps) if next_steps else 'N/A'}
"""
            parts.append(meeting_info)
        
        return "\n".join(parts)
    
    async def generate_battlecard(
        self,
        company_data: Optional[Dict[str, Any]] = None,
        contact_data: Optional[Dict[str, Any]] = None,
        product_ids: Optional[List[str]] = None,
        previous_meetings: Optional[List[Dict[str, Any]]] = None,
        meeting_notes: Optional[str] = None,
        use_deep_research: bool = True,
        deep_research: Optional[Dict[str, Any]] = None,
    ) -> Battlecard:
        """
        Generate a comprehensive battlecard for meeting preparation.
        
        Args:
            company_data: Company masterdata with research
            contact_data: Contact information
            product_ids: List of product IDs to discuss
            previous_meetings: Previous meeting records
            meeting_notes: Optional notes from the user
            use_deep_research: Whether to use/trigger deep research
            deep_research: Pre-fetched deep research data (optional)
            
        Returns:
            Battlecard object
        """
        # Get or trigger deep research if needed
        research_data = deep_research
        if use_deep_research and not research_data and company_data:
            # Check if we have cached deep research
            deep_research_cached = company_data.get('deep_research')
            if deep_research_cached:
                research_data = deep_research_cached.get('data')
            
            # If no cached research or it's old (>7 days), trigger new research
            if not research_data:
                logger.info(f"Triggering deep research for {company_data.get('name', 'Unknown')}")
                research_result = await self._deep_research_service.conduct_research(
                    company_name=company_data.get('name', ''),
                    company_website=company_data.get('domain') or company_data.get('website_url'),
                    company_industry=company_data.get('industry'),
                    company_location=company_data.get('location'),
                )
                research_data = research_result.to_dict()
        
        # Build context
        company_context = self._format_company_research(company_data, research_data)
        contact_context = self._format_contact_info(contact_data)
        product_context = self._get_product_context(product_ids or [])
        meetings_context = self._format_previous_meetings(previous_meetings or [])
        
        user_prompt = f"""## Company Research
{company_context}

## Contact Information
{contact_context}

## Products to Discuss
{product_context}

## Previous Meetings
{meetings_context}

{f'## Additional Notes from User{chr(10)}{meeting_notes}' if meeting_notes else ''}

Generate a comprehensive battlecard to prepare for this meeting."""
        
        try:
            response = await self._openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": BATTLECARD_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
                max_tokens=3000,
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Parse sections
            def parse_section(data: Optional[Dict]) -> Optional[BattlecardSection]:
                if not data:
                    return None
                return BattlecardSection(
                    title=data.get("title", ""),
                    content=data.get("content", ""),
                    bullet_points=data.get("bullet_points", []),
                )
            
            return Battlecard(
                generated_at=datetime.utcnow(),
                company_snapshot=parse_section(result.get("company_snapshot")),
                contact_snapshot=parse_section(result.get("contact_snapshot")),
                why_now_product_fit=parse_section(result.get("why_now_product_fit")),
                talking_points=result.get("talking_points", []),
                likely_objections=result.get("likely_objections", []),
                discovery_questions=result.get("discovery_questions", []),
                proof_points=result.get("proof_points", []),
                recommended_agenda=result.get("recommended_agenda"),
                key_risks=result.get("key_risks", []),
                suggested_questions=result.get("discovery_questions", []),
                suggested_next_steps=result.get("suggested_next_steps", []),
            )
            
        except Exception as e:
            logger.error(f"Error generating battlecard: {e}")
            return Battlecard(
                generated_at=datetime.utcnow(),
                key_risks=[f"Error generating battlecard: {str(e)}"],
            )
    
    async def generate_battlecard_for_meeting(
        self,
        meeting_id: str,
        meetings_dao,
        companies_dao=None,
        contacts_dao=None,
    ) -> Battlecard:
        """
        Generate battlecard for an existing meeting record.
        
        Args:
            meeting_id: Meeting ID
            meetings_dao: MeetingsDao instance
            companies_dao: CompaniesDao instance (optional)
            contacts_dao: ContactsDao instance (optional)
            
        Returns:
            Generated Battlecard
        """
        # Fetch meeting
        meeting_data = await meetings_dao.get_meeting(meeting_id)
        if not meeting_data:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        # Fetch company data
        company_data = None
        if companies_dao and meeting_data.get("company_id"):
            company_data = await companies_dao.get_company(str(meeting_data["company_id"]))
        
        # Fetch contact data
        contact_data = None
        if contacts_dao and meeting_data.get("contact_ids"):
            contact_id = str(meeting_data["contact_ids"][0])
            contact_data = await contacts_dao.get_contact(contact_id)
        
        # Fetch previous meetings
        previous_meetings = []
        if meeting_data.get("company_id"):
            previous = await meetings_dao.get_previous_meetings(
                company_id=str(meeting_data["company_id"]),
                exclude_meeting_id=meeting_id,
            )
            previous_meetings = previous
        
        # Get deep research if available
        deep_research = None
        if company_data:
            deep_research_cached = company_data.get('deep_research')
            if deep_research_cached:
                deep_research = deep_research_cached.get('data')
        
        # Generate battlecard
        battlecard = await self.generate_battlecard(
            company_data=company_data,
            contact_data=contact_data,
            product_ids=meeting_data.get("product_ids", []),
            previous_meetings=previous_meetings,
            meeting_notes=meeting_data.get("notes"),
            use_deep_research=True,
            deep_research=deep_research,
        )
        
        # Save to meeting
        await meetings_dao.set_battlecard(meeting_id, battlecard.model_dump())
        
        return battlecard

