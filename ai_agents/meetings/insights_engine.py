"""Live Insights Engine for real-time call intelligence."""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from openai import AsyncOpenAI

from config.loaded_config import loaded_config
from ai_agents.meetings.models import (
    LiveInsight,
    InsightType,
    TranscriptEntry,
    InsightGenerationContext,
    CompanyContext,
    ProductContext,
    ContactContext,
    PreviousMeetingContext,
)

logger = logging.getLogger(__name__)


# Trigger keywords for different insight types
TRIGGER_KEYWORDS = {
    InsightType.OBJECTION: [
        "budget", "expensive", "cost too", "not sure", "concern", "worried",
        "hesitant", "don't think", "can't afford", "too much", "risky",
        "not ready", "need to think", "skeptical", "uncertain"
    ],
    InsightType.BUYING_SIGNAL: [
        "when can we", "timeline", "how soon", "next steps", "get started",
        "implement", "roll out", "pricing", "contract", "proposal",
        "decision", "move forward", "interested in", "like to try"
    ],
    InsightType.COMPETITOR: [
        "sap", "oracle", "salesforce", "hubspot", "shopify", "magento",
        "woocommerce", "bigcommerce", "currently using", "other vendor",
        "alternative", "compared to", "vs", "versus"
    ],
    InsightType.PRICING_QUESTION: [
        "how much", "what's the cost", "pricing", "price", "budget",
        "investment", "roi", "return on", "payback", "total cost"
    ],
    InsightType.RISK_FLAG: [
        "confused", "don't understand", "unclear", "what do you mean",
        "not following", "lost me", "need clarification", "who else",
        "other stakeholders", "not the decision", "check with"
    ],
    InsightType.ACTION_ITEM: [
        "send me", "follow up", "schedule", "set up", "book a",
        "i'll", "we'll", "let's", "share with", "get back to"
    ],
}


INSIGHTS_SYSTEM_PROMPT = """You are a real-time sales intelligence assistant. Analyze the live call transcript and provide actionable insights for the sales rep.

Available context:
- Company research: {company_research}
- Product details: {products}
- Contact persona: {contact}
- Previous meetings: {previous_meetings}

Generate insights ONLY when you detect significant moments. Each insight must be:
1. Immediately actionable
2. Grounded in the transcript (cite specific quote)
3. Enhanced by the provided context

Insight types to detect:
- OBJECTION: Concern, hesitation, or pushback → Provide response framing
- BUYING_SIGNAL: Interest, urgency, timeline mention → Recommend next question
- COMPETITOR: Competitor name or comparison → Suggest differentiation points
- PRICING_QUESTION: Budget/cost discussion → Provide guidance + clarifying prompts
- PRODUCT_OPPORTUNITY: Feature need matching our product → Suggest mention
- RISK_FLAG: Confusion, misfit, missing stakeholder → Alert with recommendation
- ACTION_ITEM: Commitment or to-do mentioned → Capture with owner

Return a JSON object with an "insights" array. Return {"insights": []} if no significant insights detected.

Example output:
{
  "insights": [
    {
      "type": "OBJECTION",
      "message": "Budget concern detected - ROI framing needed",
      "suggested_response": "I understand budget is a consideration. Companies like yours typically see ROI within 3-6 months through reduced manual work and faster order processing.",
      "evidence": "We're not sure if we can afford this right now",
      "confidence": 0.85
    }
  ]
}
"""


class InsightsEngine:
    """
    Engine for generating real-time insights during live calls.
    
    Features:
    - Keyword-based trigger detection
    - Time-based insight generation
    - Context-aware LLM analysis
    - Insight deduplication
    """
    
    def __init__(self, context: InsightGenerationContext = None):
        """
        Initialize the insights engine.
        
        Args:
            context: Pre-loaded context for insight generation
        """
        self.context = context or InsightGenerationContext()
        self._openai_client = AsyncOpenAI(api_key=loaded_config.openai_api_key)
        self._transcript_buffer: List[TranscriptEntry] = []
        self._last_insight_time: float = 0
        self._generated_insights: List[LiveInsight] = []
        self._insight_hashes: set = set()  # For deduplication
        
        # Configuration
        self.time_trigger_seconds = 30  # Generate insights every 30 seconds
        self.max_transcript_tokens = 800  # Approximate tokens for recent transcript
        self.min_confidence_threshold = 0.6
        
    def set_context(self, context: InsightGenerationContext):
        """Update the insight generation context."""
        self.context = context
        
    def add_transcript_entry(self, entry: TranscriptEntry):
        """Add a transcript entry to the buffer."""
        self._transcript_buffer.append(entry)
        
    def get_recent_transcript(self, max_entries: int = 20) -> List[TranscriptEntry]:
        """Get recent transcript entries."""
        return self._transcript_buffer[-max_entries:]
    
    def check_triggers(self, text: str) -> List[InsightType]:
        """
        Check if text contains trigger keywords.
        
        Args:
            text: Text to check for triggers
            
        Returns:
            List of triggered insight types
        """
        text_lower = text.lower()
        triggered_types = []
        
        for insight_type, keywords in TRIGGER_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    triggered_types.append(insight_type)
                    break
        
        return triggered_types
    
    def should_generate_insights(self, current_time: float, text: str = None) -> bool:
        """
        Check if insights should be generated.
        
        Args:
            current_time: Current timestamp in seconds
            text: Optional text to check for keyword triggers
            
        Returns:
            True if insights should be generated
        """
        # Time-based trigger
        if current_time - self._last_insight_time >= self.time_trigger_seconds:
            return True
        
        # Keyword-based trigger
        if text and self.check_triggers(text):
            return True
        
        return False
    
    def _build_prompt_context(self) -> Dict[str, str]:
        """Build context strings for the prompt."""
        # Company research
        company_str = "Not available"
        if self.context.company_research:
            cr = self.context.company_research
            company_str = f"""
About: {cr.about or 'N/A'}
Industry: {cr.industry or 'N/A'}
Recent News: {', '.join(cr.recent_news) if cr.recent_news else 'N/A'}
Key Initiatives: {', '.join(cr.key_initiatives) if cr.key_initiatives else 'N/A'}
Tech Stack: {', '.join(cr.tech_stack) if cr.tech_stack else 'N/A'}
Pain Points: {', '.join(cr.pain_points_inferred) if cr.pain_points_inferred else 'N/A'}
"""
        
        # Products
        products_str = "Not specified"
        if self.context.products:
            products_list = []
            for p in self.context.products:
                product_info = f"""
- {p.name}:
  Features: {', '.join(p.key_features) if p.key_features else 'N/A'}
  Differentiators: {', '.join(p.differentiators) if p.differentiators else 'N/A'}
  Common Objections: {json.dumps(p.common_objections) if p.common_objections else 'N/A'}
"""
                products_list.append(product_info)
            products_str = "\n".join(products_list)
        
        # Contact
        contact_str = "Not available"
        if self.context.contact:
            c = self.context.contact
            contact_str = f"""
Name: {c.name}
Title: {c.title or 'N/A'}
Persona: {c.persona_insights or 'N/A'}
Previous Interactions: {', '.join(c.previous_interactions) if c.previous_interactions else 'None'}
"""
        
        # Previous meetings
        prev_meetings_str = "No previous meetings"
        if self.context.previous_meetings:
            meetings_list = []
            for m in self.context.previous_meetings:
                meeting_info = f"""
- Date: {m.date}
  Summary: {m.summary or 'N/A'}
  Objections: {', '.join(m.objections_raised) if m.objections_raised else 'None'}
  Next Steps Agreed: {', '.join(m.next_steps_agreed) if m.next_steps_agreed else 'None'}
"""
                meetings_list.append(meeting_info)
            prev_meetings_str = "\n".join(meetings_list)
        
        return {
            "company_research": company_str,
            "products": products_str,
            "contact": contact_str,
            "previous_meetings": prev_meetings_str,
        }
    
    def _format_transcript_for_prompt(self) -> str:
        """Format recent transcript for the LLM prompt."""
        recent = self.get_recent_transcript()
        lines = []
        for entry in recent:
            timestamp_str = f"[{entry.timestamp:.1f}s]"
            speaker = "You" if entry.speaker == "user" else "Client"
            lines.append(f"{timestamp_str} {speaker}: {entry.text}")
        return "\n".join(lines)
    
    def _create_insight_hash(self, insight_type: str, message: str) -> str:
        """Create a hash for deduplication."""
        # Simple hash based on type and key words
        key_words = sorted(set(message.lower().split()))[:5]
        return f"{insight_type}:{'_'.join(key_words)}"
    
    async def generate_insights(self, current_time: float) -> List[LiveInsight]:
        """
        Generate insights from the current transcript and context.
        
        Args:
            current_time: Current timestamp in seconds
            
        Returns:
            List of new insights
        """
        if not self._transcript_buffer:
            return []
        
        self._last_insight_time = current_time
        
        # Build the prompt
        context_parts = self._build_prompt_context()
        system_prompt = INSIGHTS_SYSTEM_PROMPT.format(**context_parts)
        
        transcript_text = self._format_transcript_for_prompt()
        user_prompt = f"""Recent conversation transcript:

{transcript_text}

Analyze this conversation and generate any relevant insights. Focus on actionable intelligence that helps the sales rep right now."""
        
        try:
            response = await self._openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1000,
            )
            
            result = json.loads(response.choices[0].message.content)
            raw_insights = result.get("insights", [])
            
            new_insights = []
            for raw in raw_insights:
                # Skip low confidence insights
                confidence = raw.get("confidence", 0.8)
                if confidence < self.min_confidence_threshold:
                    continue
                
                # Check for duplicates
                insight_hash = self._create_insight_hash(
                    raw.get("type", ""),
                    raw.get("message", "")
                )
                if insight_hash in self._insight_hashes:
                    continue
                
                # Create insight object
                try:
                    insight_type = InsightType(raw.get("type", "").lower())
                except ValueError:
                    insight_type = InsightType.RISK_FLAG
                
                insight = LiveInsight(
                    id=str(uuid.uuid4()),
                    timestamp=current_time,
                    type=insight_type,
                    message=raw.get("message", "")[:80],  # Max 80 chars
                    suggested_response=raw.get("suggested_response", ""),
                    evidence=raw.get("evidence", ""),
                    confidence=confidence,
                    is_pinned=False,
                    is_action_item=insight_type == InsightType.ACTION_ITEM,
                )
                
                self._insight_hashes.add(insight_hash)
                self._generated_insights.append(insight)
                new_insights.append(insight)
            
            logger.info(f"Generated {len(new_insights)} new insights")
            return new_insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    async def generate_post_call_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive post-call summary.
        
        Returns:
            Dictionary with summary, key points, action items, next steps
        """
        if not self._transcript_buffer:
            return {
                "summary": "No transcript available",
                "key_discussion_points": [],
                "action_items": [],
                "next_steps": [],
                "objections_resolutions": [],
            }
        
        context_parts = self._build_prompt_context()
        transcript_text = self._format_transcript_for_prompt()
        
        # Include generated insights in the summary
        insights_text = ""
        if self._generated_insights:
            insights_list = []
            for ins in self._generated_insights:
                insights_list.append(f"- [{ins.type.value}] {ins.message}")
            insights_text = "\n".join(insights_list)
        
        system_prompt = """You are a sales call analyst. Generate a comprehensive post-call summary.

Return a JSON object with:
{
  "summary": "2-3 paragraph summary of the call",
  "key_discussion_points": ["point 1", "point 2", ...],
  "action_items": [{"text": "action", "owner": "person or 'us'/'them'"}],
  "next_steps": ["step 1", "step 2", ...],
  "objections_resolutions": [{"objection": "...", "resolution": "..."}],
  "products_discussed": ["product 1", ...]
}
"""
        
        user_prompt = f"""Company Context:
{context_parts['company_research']}

Products Discussed:
{context_parts['products']}

Contact:
{context_parts['contact']}

Full Transcript:
{transcript_text}

Insights Detected During Call:
{insights_text if insights_text else 'None'}

Generate a comprehensive post-call summary."""
        
        try:
            response = await self._openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000,
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error generating post-call summary: {e}")
            return {
                "summary": f"Error generating summary: {str(e)}",
                "key_discussion_points": [],
                "action_items": [],
                "next_steps": [],
                "objections_resolutions": [],
            }
    
    def get_all_insights(self) -> List[LiveInsight]:
        """Get all generated insights."""
        return self._generated_insights
    
    def clear(self):
        """Clear all buffers and reset state."""
        self._transcript_buffer = []
        self._last_insight_time = 0
        self._generated_insights = []
        self._insight_hashes = set()

