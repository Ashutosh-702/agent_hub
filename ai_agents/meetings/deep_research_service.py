"""Deep Research Service for meeting preparation."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI

from config.loaded_config import loaded_config

logger = logging.getLogger(__name__)


DEEP_RESEARCH_SYSTEM_PROMPT = """You are a business intelligence researcher specializing in company deep research for sales meetings.

Your task is to conduct comprehensive research about a company and provide structured analysis that will help sales teams prepare for meetings.

RESEARCH OBJECTIVES:
1. **Company Overview** - Comprehensive description of what the company does, their business model, market position
2. **Recent News & Signals** - Important recent developments including:
   - Funding rounds (indicates growth mode, budget availability)
   - Leadership changes (new decision makers, organizational shifts)
   - Expansion plans (increased complexity, growth opportunities)
   - Digital transformation initiatives (tech investment signals)
   - Layoffs or cost-cutting (budget constraints)
   - M&A activity (system consolidation needs)
   - Product launches (growth indicators)
   - Partnerships (strategic direction)
3. **Key Initiatives** - Current strategic priorities and projects
4. **Tech Stack** - Technologies and platforms they use (helps with integration discussions)
5. **Inferred Pain Points** - Likely challenges based on industry, size, and recent news
6. **Competitive Landscape** - Who they compete with and market position

Use web search to find:
- Company website and about page
- Recent news articles and press releases
- LinkedIn company page
- Industry reports mentioning the company
- Funding announcements (Crunchbase, TechCrunch, etc.)
- Leadership changes (LinkedIn, news)
- Expansion announcements
- Tech stack information (StackShare, job postings)

Return a JSON object with this structure:
{
  "company_overview": "2-3 paragraph comprehensive overview",
  "recent_news": [
    {
      "title": "News headline",
      "date": "YYYY-MM-DD or relative (e.g., '3 months ago')",
      "summary": "Brief summary",
      "signal_type": "funding|expansion|leadership_change|layoffs|partnership|product_launch|other",
      "implication": "Why this matters for sales (budget, urgency, decision makers, etc.)"
    }
  ],
  "key_initiatives": ["initiative 1", "initiative 2", ...],
  "tech_stack": ["technology 1", "technology 2", ...],
  "inferred_pain_points": ["pain point 1", "pain point 2", ...],
  "competitive_landscape": "Brief description of market position and competitors"
}

Be specific and actionable. Focus on signals that indicate buying intent, budget availability, and decision-making urgency."""


class NewsSignal:
    """Represents a news signal with implications for sales."""
    
    def __init__(
        self,
        title: str,
        date: str,
        summary: str,
        signal_type: str,
        implication: str,
    ):
        self.title = title
        self.date = date
        self.summary = summary
        self.signal_type = signal_type
        self.implication = implication
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "date": self.date,
            "summary": self.summary,
            "signal_type": self.signal_type,
            "implication": self.implication,
        }


class DeepResearchResult:
    """Result of deep research analysis."""
    
    def __init__(
        self,
        company_overview: str,
        recent_news: List[Dict[str, Any]],
        key_initiatives: List[str],
        inferred_pain_points: List[str],
        tech_stack: List[str],
        competitive_landscape: str,
        research_date: datetime,
    ):
        self.company_overview = company_overview
        self.recent_news = recent_news
        self.key_initiatives = key_initiatives
        self.inferred_pain_points = inferred_pain_points
        self.tech_stack = tech_stack
        self.competitive_landscape = competitive_landscape
        self.research_date = research_date
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_overview": self.company_overview,
            "recent_news": self.recent_news,
            "key_initiatives": self.key_initiatives,
            "inferred_pain_points": self.inferred_pain_points,
            "tech_stack": self.tech_stack,
            "competitive_landscape": self.competitive_landscape,
            "research_date": self.research_date.isoformat(),
        }


class DeepResearchService:
    """
    Service for conducting deep company research for meeting preparation.
    
    Uses OpenAI with web search capabilities to gather:
    - Company overview
    - Recent news and signals
    - Key initiatives
    - Tech stack
    - Inferred pain points
    - Competitive landscape
    """
    
    def __init__(self):
        """Initialize the deep research service."""
        api_key = loaded_config.openai_api_key
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables. Deep research will fail.")
        self._openai_client = AsyncOpenAI(api_key=api_key) if api_key else None
    
    async def conduct_research(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        company_industry: Optional[str] = None,
        company_location: Optional[str] = None,
    ) -> DeepResearchResult:
        """
        Conduct deep research on a company.
        
        Args:
            company_name: Company name
            company_website: Company website (optional)
            company_industry: Company industry (optional)
            company_location: Company location (optional)
            
        Returns:
            DeepResearchResult with comprehensive analysis
        """
        user_prompt = f"""COMPANY TO RESEARCH:
- Name: {company_name}
- Website: {company_website or 'Unknown - FIND IT'}
- Industry: {company_industry or 'Unknown - DETERMINE IT'}
- Location: {company_location or 'Unknown - FIND IT'}

Conduct comprehensive research using web search. Focus on:
1. Recent news and developments (last 6-12 months)
2. Funding, expansion, leadership changes
3. Tech stack and digital initiatives
4. Market position and competitors
5. Likely pain points based on industry and size

Provide detailed, actionable intelligence that will help prepare for a sales meeting."""
        
        try:
            # Check if OpenAI client has web search capabilities
            # For OpenAI models with web search, we can use function calling or tools
            # For now, we'll use a direct approach with instructions to use web search
            
            response = await self._openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": DEEP_RESEARCH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=3000,
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Parse result into DeepResearchResult
            research_result = DeepResearchResult(
                company_overview=result.get("company_overview", "Research incomplete"),
                recent_news=result.get("recent_news", []),
                key_initiatives=result.get("key_initiatives", []),
                inferred_pain_points=result.get("inferred_pain_points", []),
                tech_stack=result.get("tech_stack", []),
                competitive_landscape=result.get("competitive_landscape", "Not available"),
                research_date=datetime.utcnow(),
            )
            
            logger.info(f"Completed deep research for {company_name}: {len(research_result.recent_news)} news signals found")
            return research_result
            
        except Exception as e:
            logger.error(f"Error conducting deep research: {e}")
            # Return minimal result on error
            return DeepResearchResult(
                company_overview=f"Research error: {str(e)}",
                recent_news=[],
                key_initiatives=[],
                inferred_pain_points=[],
                tech_stack=[],
                competitive_landscape="Research unavailable",
                research_date=datetime.utcnow(),
            )
    
    def get_important_signals(self, research_result: DeepResearchResult) -> List[Dict[str, Any]]:
        """
        Extract the most important signals from research.
        
        Prioritizes signals that indicate:
        - Budget availability (funding, growth)
        - Urgency (expansion, digital transformation)
        - Decision makers (leadership changes)
        - Pain points (layoffs, cost-cutting)
        
        Args:
            research_result: DeepResearchResult to analyze
            
        Returns:
            List of important signals sorted by priority
        """
        important_types = ["funding", "expansion", "digital_transformation", "leadership_change"]
        
        important_signals = [
            news for news in research_result.recent_news
            if news.get("signal_type") in important_types
        ]
        
        # Sort by date (most recent first) and type priority
        type_priority = {
            "funding": 1,
            "expansion": 2,
            "digital_transformation": 3,
            "leadership_change": 4,
        }
        
        important_signals.sort(
            key=lambda x: (
                type_priority.get(x.get("signal_type", ""), 99),
                x.get("date", "")
            )
        )
        
        return important_signals[:5]  # Top 5 most important

