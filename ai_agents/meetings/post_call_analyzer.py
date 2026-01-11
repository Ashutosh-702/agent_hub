"""Post-Call Analysis Service using OpenAI."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI

from config.loaded_config import loaded_config

logger = logging.getLogger(__name__)


ANALYSIS_SYSTEM_PROMPT = """You are a sales meeting analyst. Analyze the meeting transcript and generate a comprehensive post-call summary.

Based on the transcript and context provided, generate:

1. **Summary** - A 2-3 paragraph executive summary of the call, highlighting key outcomes, overall sentiment, and main discussion points.

2. **Key Discussion Points** - 5-7 bullet points covering the main topics discussed, decisions made, and important information shared.

3. **Objections & Resolutions** - List any objections, concerns, or pushback raised during the call, and how they were addressed (or if they remain open).

4. **Action Items** - Tasks mentioned or agreed upon, with suggested owners (us/them) and timelines if mentioned.

5. **Next Steps** - Agreed or recommended next steps to move the deal forward.

6. **Follow-up Message Draft** - A ready-to-send email draft to the client summarizing the meeting and next steps.

Return a JSON object with this structure:
{
  "summary": "2-3 paragraph executive summary",
  "key_discussion_points": ["point 1", "point 2", ...],
  "objections_resolutions": [
    {"objection": "objection text", "resolution": "how it was addressed or if open"}
  ],
  "action_items": [
    {"text": "action description", "owner": "us or them", "due_date": "suggested date if mentioned"}
  ],
  "next_steps": ["step 1", "step 2", ...],
  "follow_up_message": {
    "subject": "Meeting Follow-up: [Company Name]",
    "body": "Complete email body ready to send"
  }
}

Be specific and actionable. Extract real information from the transcript."""


class PostCallAnalyzer:
    """
    Service for analyzing completed meetings using OpenAI.
    
    Generates:
    - Executive summary
    - Key discussion points
    - Objections & resolutions
    - Action items
    - Next steps
    - Follow-up email draft
    """
    
    def __init__(self):
        """Initialize the post-call analyzer."""
        api_key = loaded_config.openai_api_key
        if not api_key:
            logger.error(f"OPENAI_API_KEY not found in environment variables. AI analysis will fail. Key value: '{api_key}'")
        else:
            logger.info(f"OpenAI API key loaded successfully (length: {len(api_key)}, starts with 'sk-': {api_key.startswith('sk-')})")
        self._openai_client = AsyncOpenAI(api_key=api_key) if api_key else None
    
    def _format_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """Format transcript for the prompt."""
        if not transcript:
            return "No transcript available"
        
        lines = []
        # Handle double-nested format if it slipped through {"transcript": [...]}
        if isinstance(transcript, dict):
            logger.warning(f"⚠️ Transcript is a dict, not a list! Keys: {transcript.keys()}")
            if "transcript" in transcript:
                transcript = transcript.get("transcript", [])
        
        for entry in transcript:
            timestamp = entry.get("timestamp", 0)
            speaker = "You" if entry.get("speaker") == "user" else "Client"
            text = entry.get("text", "")
            lines.append(f"[{timestamp:.1f}s] {speaker}: {text}")
        
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
            if not name:
                name = contact_data.get('name', 'Unknown')
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
                    date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else str(date)[:10]
                else:
                    date_str = "Unknown date"
                summary = pm.get('summary', 'No summary')[:200]
                parts.append(f"- {date_str}: {summary}")
        
        return "\n".join(parts) if parts else "No additional context available"
    
    async def analyze_meeting(
        self,
        transcript: List[Dict[str, Any]],
        company_data: Optional[Dict[str, Any]] = None,
        contact_data: Optional[Dict[str, Any]] = None,
        products: Optional[List[str]] = None,
        previous_meetings: Optional[List[Dict[str, Any]]] = None,
        company_name: str = "",
    ) -> Dict[str, Any]:
        """
        Analyze a completed meeting and generate post-call summary.
        
        Args:
            transcript: List of transcript entries
            company_data: Company masterdata
            contact_data: Contact information
            products: Products discussed
            previous_meetings: Previous meeting records
            company_name: Company name for follow-up email
            
        Returns:
            Dictionary with summary, key points, objections, action items, next steps, and follow-up draft
        """
        if not transcript:
            return {
                "summary": "No transcript available for analysis.",
                "key_discussion_points": [],
                "objections_resolutions": [],
                "action_items": [],
                "next_steps": [],
                "follow_up_message": {
                    "subject": "Meeting Follow-up",
                    "body": "Thank you for your time today."
                }
            }
        
        # Format inputs for prompt
        transcript_text = self._format_transcript(transcript)
        context_text = self._format_context(
            company_data, contact_data, products, previous_meetings
        )
        
        # Debug logging to see what's being sent to OpenAI
        logger.info(f"📝 Analyzing meeting with transcript entries: {len(transcript)}")
        logger.info(f"📝 Transcript preview: {transcript_text[:500] if transcript_text else 'EMPTY'}")
        logger.info(f"📝 Context: {context_text[:500] if context_text else 'EMPTY'}")
        
        user_prompt = f"""## Meeting Context
{context_text}

## Meeting Transcript
{transcript_text}

Analyze this meeting and generate a comprehensive post-call summary with all requested sections."""
        
        if not self._openai_client:
            return {
                "summary": "Error: OpenAI API key not configured. Please set OPENAI_API_KEY in .env file.",
                "key_discussion_points": [],
                "objections_resolutions": [],
                "action_items": [],
                "next_steps": [],
                "follow_up_message": {
                    "subject": "Meeting Follow-up",
                    "body": "Thank you for your time today."
                }
            }
        
        try:
            response = await self._openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000,
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Ensure all required fields exist
            analysis = {
                "summary": result.get("summary", "Summary not available"),
                "key_discussion_points": result.get("key_discussion_points", []),
                "objections_resolutions": result.get("objections_resolutions", []),
                "action_items": result.get("action_items", []),
                "next_steps": result.get("next_steps", []),
                "follow_up_message": result.get("follow_up_message", {
                    "subject": f"Meeting Follow-up: {company_name}" if company_name else "Meeting Follow-up",
                    "body": "Thank you for your time today."
                }),
            }
            
            # Update follow-up subject with company name if provided
            if company_name and analysis["follow_up_message"].get("subject"):
                if "Meeting Follow-up" in analysis["follow_up_message"]["subject"]:
                    analysis["follow_up_message"]["subject"] = f"Meeting Follow-up: {company_name}"
            
            logger.info(f"Generated post-call analysis with {len(analysis['key_discussion_points'])} key points")
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating post-call analysis: {e}")
            return {
                "summary": f"Error generating analysis: {str(e)}",
                "key_discussion_points": [],
                "objections_resolutions": [],
                "action_items": [],
                "next_steps": [],
                "follow_up_message": {
                    "subject": "Meeting Follow-up",
                    "body": "Thank you for your time today."
                }
            }

