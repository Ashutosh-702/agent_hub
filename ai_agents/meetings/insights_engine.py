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
        "alternative", "compared to", "vs", "versus", "unicommerce",
        "increff", "vinculum", "manhattan", "lightspeed", "square"
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
    InsightType.DISCOVERY_QUESTION: [
        "challenge", "problem", "pain", "struggle", "difficult", "issue",
        "bottleneck", "frustration", "slow", "manual", "inefficient"
    ],
    InsightType.VALUE_PROP: [
        "benefit", "advantage", "help", "improve", "solve", "achieve",
        "goal", "objective", "target", "success", "growth", "scale"
    ],
    InsightType.PRODUCT_FEATURE: [
        "feature", "capability", "function", "can it", "does it",
        "integration", "api", "mobile", "real-time", "automation"
    ],
}


INSIGHTS_SYSTEM_PROMPT = """You are an elite real-time sales coach helping a Fynd sales rep close deals. Your goal is to maximize conversion by providing actionable suggestions based on the live conversation, company research, and product knowledge.

## CONTEXT

**Company Research:**
{company_research}

**Products Being Discussed:**
{products}

**Contact Information:**
{contact}

**Previous Meetings:**
{previous_meetings}

## YOUR MISSION

Analyze the conversation and provide 1-3 high-impact suggestions that will help the sales rep:
1. Uncover more pain points (discovery questions)
2. Connect client needs to Fynd product capabilities (value propositions)
3. Handle objections effectively (objection responses)
4. Highlight relevant product features (product features)
5. Identify buying signals and risks (signals)

## INSIGHT TYPES

- **DISCOVERY_QUESTION**: Suggest a probing question to uncover pain points. Base it on what the client just said + company research. Example: "Ask about their current order cancellation rate since they mentioned inventory issues"

- **VALUE_PROP**: Suggest a value proposition that connects their stated need to Fynd's solution. Use specific product features and case studies. Example: "Highlight how Fynd OMS reduced order cancellations by 40% for similar retailers"

- **OBJECTION**: When you detect hesitation or pushback, provide a response framework. Use evidence from case studies and ROI data. Example: "Address pricing concern with ROI timeline - typical payback in 3-6 months"

- **PRODUCT_FEATURE**: When the client mentions a need, suggest a specific feature to highlight. Be specific about the capability. Example: "Mention real-time inventory sync across 50+ channels"

- **BUYING_SIGNAL**: When you detect interest or urgency, suggest how to capitalize. Recommend next step or closing question. Example: "Strong interest detected - ask about their decision timeline"

- **COMPETITOR**: When a competitor is mentioned, provide differentiation points. Use specific advantages from product knowledge. Example: "Counter Unicommerce mention with native OMS+WMS integration advantage"

- **RISK_FLAG**: Alert to potential deal risks. Identify missing stakeholders, confusion, or misfit signals. Example: "Prospect seems confused about integration - clarify API-first architecture"

- **ACTION_ITEM**: Capture commitments made during the call. Note the owner and deadline if mentioned.

## RULES

1. ALWAYS ground suggestions in the actual conversation (cite what was said)
2. ALWAYS use specific product features, case studies, or data points when available
3. Keep message short (max 80 chars) - the suggested_response can be longer
4. Provide suggested_response with actual words the rep can say
5. Only generate insights when there's something actionable - quality over quantity
6. Focus on insights that increase conversion probability

## OUTPUT FORMAT

Return JSON with "insights" array. Return {{"insights": []}} if no actionable insights.

```json
{{
  "insights": [
    {{
      "type": "DISCOVERY_QUESTION",
      "message": "Probe deeper on inventory challenges mentioned",
      "suggested_response": "You mentioned inventory discrepancies - what's the impact on your order cancellation rate? Many retailers we work with see 10-15% cancellations from this.",
      "evidence": "We're struggling with inventory visibility",
      "confidence": 0.9
    }},
    {{
      "type": "VALUE_PROP", 
      "message": "Connect their omnichannel goal to Fynd OMS",
      "suggested_response": "For true omnichannel, you need real-time inventory sync and intelligent order routing. Our OMS handles ship-from-store, BOPIS, and split shipping automatically.",
      "evidence": "We want to enable buy online pickup in store",
      "confidence": 0.85
    }}
  ]
}}
```
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
        api_key = loaded_config.openai_api_key
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables. Insights generation will fail.")
        self._openai_client = AsyncOpenAI(api_key=api_key) if api_key else None
        self._transcript_buffer: List[TranscriptEntry] = []
        self._last_insight_time: float = 0
        self._generated_insights: List[LiveInsight] = []
        self._insight_hashes: set = set()  # For deduplication
        
        # Configuration
        self.time_trigger_seconds = 20  # Generate insights every 20 seconds
        self.max_transcript_tokens = 1000  # Approximate tokens for recent transcript
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
        # If _last_insight_time is 0, it means no insights have been generated yet
        # In that case, only generate if we have transcript content
        if self._last_insight_time == 0:
            # First generation - only if we have transcript content
            if self._transcript_buffer:
                return True
            return False
        
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
            logger.warning("⚠️ No transcript buffer - cannot generate insights")
            return []
        
        buffer_size = len(self._transcript_buffer)
        logger.info(f"🔄 GENERATING INSIGHTS - buffer: {buffer_size} entries, last insight time: {self._last_insight_time:.1f}s, current time: {current_time:.1f}s")
        
        # Update last insight time AFTER successful generation (moved to end of method)
        # self._last_insight_time = current_time  # Moved to after API call
        
        # Build the prompt
        context_parts = self._build_prompt_context()
        system_prompt = INSIGHTS_SYSTEM_PROMPT.format(**context_parts)
        
        transcript_text = self._format_transcript_for_prompt()
        user_prompt = f"""Recent conversation transcript:

{transcript_text}

Analyze this conversation and generate any relevant insights. Focus on actionable intelligence that helps the sales rep right now."""
        
        if not self._openai_client:
            logger.error("❌ OpenAI client not initialized - cannot generate insights. Check OPENAI_API_KEY environment variable.")
            return []
        
        try:
            logger.debug(f"Calling OpenAI API with {len(self._transcript_buffer)} transcript entries")
            logger.debug(f"System prompt length: {len(system_prompt)} chars")
            logger.debug(f"User prompt length: {len(user_prompt)} chars")
            
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
            
            logger.debug(f"OpenAI API response received: {response.choices[0].message.content[:200]}...")
            
            result = json.loads(response.choices[0].message.content)
            raw_insights = result.get("insights", [])
            
            logger.info(f"📥 OpenAI returned {len(raw_insights)} raw insights")
            
            if not raw_insights:
                logger.warning(f"⚠️ No insights in OpenAI response at {current_time:.1f}s - may be normal if conversation is too short or no actionable items")
                logger.debug(f"   Transcript buffer size: {len(self._transcript_buffer)}, Last insight time: {self._last_insight_time:.1f}s")
            
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
                raw_type = raw.get("type", "").lower()
                try:
                    # Map common variations to enum values
                    type_mapping = {
                        "discovery_question": InsightType.DISCOVERY_QUESTION,
                        "value_prop": InsightType.VALUE_PROP,
                        "value_proposition": InsightType.VALUE_PROP,
                        "product_feature": InsightType.PRODUCT_FEATURE,
                        "objection": InsightType.OBJECTION,
                        "buying_signal": InsightType.BUYING_SIGNAL,
                        "competitor": InsightType.COMPETITOR,
                        "pricing_question": InsightType.PRICING_QUESTION,
                        "product_opportunity": InsightType.PRODUCT_OPPORTUNITY,
                        "risk_flag": InsightType.RISK_FLAG,
                        "action_item": InsightType.ACTION_ITEM,
                    }
                    insight_type = type_mapping.get(raw_type, InsightType(raw_type))
                except (ValueError, KeyError) as e:
                    logger.warning(f"Unknown insight type '{raw_type}', defaulting to RISK_FLAG: {e}")
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
            
            logger.info(f"✅ Generated {len(new_insights)} new insights from {len(raw_insights)} raw insights")
            
            if len(new_insights) == 0 and len(raw_insights) > 0:
                logger.warning(f"⚠️ All {len(raw_insights)} raw insights were filtered out (low confidence, duplicates, or invalid types)")
            
            # Update last insight time only after successful generation
            self._last_insight_time = current_time
            logger.debug(f"Updated _last_insight_time to {current_time:.1f}s")
            
            return new_insights
            
        except Exception as e:
            logger.error(f"❌ Error generating insights: {e}", exc_info=True)
            # Don't update _last_insight_time on error, so we can retry
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

