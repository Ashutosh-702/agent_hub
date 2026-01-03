"""Post-call AI Reflections Generator."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI

from config.loaded_config import loaded_config
from ai_agents.meetings.models import (
    AIReflections,
    RecommendedFollowUp,
    RelationshipStatus,
    Priority,
    MeetingRecord,
    LiveInsight,
    InsightType,
)

logger = logging.getLogger(__name__)


REFLECTIONS_SYSTEM_PROMPT = """You are a sales performance coach analyzing a completed sales call. Generate thoughtful, actionable post-call reflections to help the sales rep improve and close the deal.

Based on the call transcript, insights detected, and context provided, generate reflections covering:

1. What Went Well - Identify 2-4 positive moments: good rapport building, effective objection handling, clear explanations, strong discovery questions

2. Areas for Improvement - Identify 2-4 opportunities: missed questions, unclear explanations, unaddressed concerns, better ways to handle objections

3. Key Learnings - New information discovered: company priorities, decision process, budget cycle, stakeholders, technical requirements

4. Relationship Status - Assess the buyer-seller relationship:
   - "cold": No engagement, skeptical
   - "warming": Some interest, still evaluating
   - "engaged": Active interest, asking good questions
   - "champion": Enthusiastic, advocating internally

5. Deal Health Score - 0-100 score based on:
   - Buying signals vs red flags
   - Decision timeline clarity
   - Budget alignment
   - Stakeholder access
   - Product fit

6. Recommended Follow-ups - Prioritized actions with timelines:
   - High: Do within 24 hours
   - Medium: Do within the week
   - Low: Nice to have

7. Competitive Positioning - If competitors were mentioned, assess our position

8. Stakeholder Analysis - Who else needs to be involved, who's the decision maker

9. Risk Assessment - Potential deal blockers

Return a JSON object with this structure:
{
  "what_went_well": ["point 1", "point 2"],
  "areas_for_improvement": ["point 1", "point 2"],
  "key_learnings": ["learning 1", "learning 2"],
  "relationship_status": "cold|warming|engaged|champion",
  "deal_health_score": 0-100,
  "recommended_follow_ups": [
    {"action": "action text", "priority": "high|medium|low", "suggested_timeline": "within 24 hours"}
  ],
  "competitive_positioning": "summary of competitive position",
  "stakeholder_analysis": "analysis of stakeholders and decision makers",
  "risk_assessment": ["risk 1", "risk 2"]
}
"""


class ReflectionsGenerator:
    """
    Generator for AI-powered post-call reflections.
    
    Analyzes completed calls to provide:
    - Performance assessment
    - Deal health scoring
    - Actionable follow-up recommendations
    - Competitive intelligence
    """
    
    def __init__(self):
        """Initialize the reflections generator."""
        self._openai_client = AsyncOpenAI(api_key=loaded_config.openai_api_key)
    
    def _format_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """Format transcript for the prompt."""
        if not transcript:
            return "No transcript available"
        
        lines = []
        for entry in transcript:
            timestamp = entry.get("timestamp", 0)
            speaker = "You" if entry.get("speaker") == "user" else "Client"
            text = entry.get("text", "")
            lines.append(f"[{timestamp:.1f}s] {speaker}: {text}")
        
        return "\n".join(lines)
    
    def _format_insights(self, insights: List[Dict[str, Any]]) -> str:
        """Format live insights for the prompt."""
        if not insights:
            return "No insights were detected during the call"
        
        lines = []
        for ins in insights:
            ins_type = ins.get("type", "unknown")
            message = ins.get("message", "")
            evidence = ins.get("evidence", "")
            lines.append(f"- [{ins_type}] {message}")
            if evidence:
                lines.append(f"  Quote: \"{evidence}\"")
        
        return "\n".join(lines)
    
    def _format_context(
        self,
        company_data: Optional[Dict[str, Any]] = None,
        contact_data: Optional[Dict[str, Any]] = None,
        products: Optional[List[str]] = None,
        previous_meetings: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Format context information for the prompt."""
        parts = []
        
        if company_data:
            parts.append(f"Company: {company_data.get('name', 'Unknown')}")
            if company_data.get('industry'):
                parts.append(f"Industry: {company_data['industry']}")
            if company_data.get('enriched_data'):
                enriched = company_data['enriched_data']
                if enriched.get('web_search_analysis', {}).get('research_summary'):
                    summary = enriched['web_search_analysis']['research_summary']
                    parts.append(f"Company Research: {json.dumps(summary, indent=2)}")
        
        if contact_data:
            name = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip()
            parts.append(f"Contact: {name}")
            if contact_data.get('job_title'):
                parts.append(f"Title: {contact_data['job_title']}")
        
        if products:
            parts.append(f"Products Discussed: {', '.join(products)}")
        
        if previous_meetings:
            parts.append("\nPrevious Meetings:")
            for pm in previous_meetings[:3]:  # Last 3 meetings
                date = pm.get('ended_at') or pm.get('created_at')
                if date:
                    date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else str(date)
                else:
                    date_str = "Unknown date"
                summary = pm.get('summary', 'No summary')[:200]
                parts.append(f"- {date_str}: {summary}")
        
        return "\n".join(parts) if parts else "No additional context available"
    
    async def generate_reflections(
        self,
        meeting: MeetingRecord = None,
        transcript: List[Dict[str, Any]] = None,
        insights: List[Dict[str, Any]] = None,
        company_data: Optional[Dict[str, Any]] = None,
        contact_data: Optional[Dict[str, Any]] = None,
        products: Optional[List[str]] = None,
        previous_meetings: Optional[List[Dict[str, Any]]] = None,
    ) -> AIReflections:
        """
        Generate AI reflections for a completed call.
        
        Args:
            meeting: MeetingRecord object (if available)
            transcript: List of transcript entries
            insights: List of live insights from the call
            company_data: Company masterdata
            contact_data: Contact information
            products: Products discussed
            previous_meetings: Previous meeting records
            
        Returns:
            AIReflections object with generated analysis
        """
        # Extract data from meeting if provided
        if meeting:
            transcript = transcript or [e.model_dump() for e in meeting.transcript]
            insights = insights or [i.model_dump() for i in meeting.live_insights]
            products = products or meeting.product_ids
        
        # Format inputs for prompt
        transcript_text = self._format_transcript(transcript or [])
        insights_text = self._format_insights(insights or [])
        context_text = self._format_context(
            company_data, contact_data, products, previous_meetings
        )
        
        user_prompt = f"""## Call Context
{context_text}

## Call Transcript
{transcript_text}

## Insights Detected During Call
{insights_text}

Generate comprehensive post-call reflections to help the sales rep improve and close this deal."""
        
        try:
            response = await self._openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": REFLECTIONS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
                max_tokens=2000,
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Parse relationship status
            relationship_status = None
            status_str = result.get("relationship_status", "").lower()
            if status_str in ["cold", "warming", "engaged", "champion"]:
                relationship_status = RelationshipStatus(status_str)
            
            # Parse recommended follow-ups
            follow_ups = []
            for fu in result.get("recommended_follow_ups", []):
                priority_str = fu.get("priority", "medium").lower()
                try:
                    priority = Priority(priority_str)
                except ValueError:
                    priority = Priority.MEDIUM
                
                follow_ups.append(RecommendedFollowUp(
                    action=fu.get("action", ""),
                    priority=priority,
                    suggested_timeline=fu.get("suggested_timeline"),
                ))
            
            return AIReflections(
                generated_at=datetime.utcnow(),
                what_went_well=result.get("what_went_well", []),
                areas_for_improvement=result.get("areas_for_improvement", []),
                key_learnings=result.get("key_learnings", []),
                relationship_status=relationship_status,
                deal_health_score=result.get("deal_health_score"),
                recommended_follow_ups=follow_ups,
                competitive_positioning=result.get("competitive_positioning"),
                stakeholder_analysis=result.get("stakeholder_analysis"),
                risk_assessment=result.get("risk_assessment", []),
            )
            
        except Exception as e:
            logger.error(f"Error generating reflections: {e}")
            return AIReflections(
                generated_at=datetime.utcnow(),
                what_went_well=[],
                areas_for_improvement=["Error generating reflections - please regenerate"],
                key_learnings=[],
                risk_assessment=[f"Generation error: {str(e)}"],
            )
    
    async def regenerate_reflections(
        self,
        meeting_id: str,
        meetings_dao,
        companies_dao=None,
        contacts_dao=None,
    ) -> AIReflections:
        """
        Regenerate reflections for an existing meeting.
        
        Args:
            meeting_id: ID of the meeting
            meetings_dao: MeetingsDao instance
            companies_dao: CompaniesDao instance (optional)
            contacts_dao: ContactsDao instance (optional)
            
        Returns:
            New AIReflections
        """
        # Fetch meeting
        meeting_data = await meetings_dao.get_meeting(meeting_id)
        if not meeting_data:
            raise ValueError(f"Meeting {meeting_id} not found")
        
        # Fetch company data if available
        company_data = None
        if companies_dao and meeting_data.get("company_id"):
            company_data = await companies_dao.get_company(str(meeting_data["company_id"]))
        
        # Fetch contact data if available
        contact_data = None
        if contacts_dao and meeting_data.get("contact_ids"):
            contact_id = str(meeting_data["contact_ids"][0])  # Primary contact
            contact_data = await contacts_dao.get_contact(contact_id)
        
        # Fetch previous meetings
        previous_meetings = []
        if meeting_data.get("company_id"):
            previous = await meetings_dao.get_previous_meetings(
                company_id=str(meeting_data["company_id"]),
                exclude_meeting_id=meeting_id,
            )
            previous_meetings = previous[:3]  # Last 3
        
        # Generate reflections
        reflections = await self.generate_reflections(
            transcript=meeting_data.get("transcript", []),
            insights=meeting_data.get("live_insights", []),
            company_data=company_data,
            contact_data=contact_data,
            products=meeting_data.get("product_ids", []),
            previous_meetings=previous_meetings,
        )
        
        # Save to meeting
        await meetings_dao.set_ai_reflections(meeting_id, reflections.model_dump())
        
        return reflections

