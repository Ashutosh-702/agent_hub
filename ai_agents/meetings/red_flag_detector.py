"""Red Flag Detection Service for sales meetings."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI

from config.loaded_config import loaded_config

logger = logging.getLogger(__name__)


RED_FLAG_SYSTEM_PROMPT = """You are a sales intelligence analyst. Analyze the meeting transcript to detect red flags that indicate low buying intent or deal risk.

Red flags to detect:

1. **Multiple 'committee' decisions** - Mentions of committees, boards, multiple approvers, group decisions
2. **Currently using spreadsheets only** - Mentions of Excel, Google Sheets, manual processes, no existing software
3. **'Exploring options' with no deadline** - Exploring/evaluating language without timeline or urgency
4. **Budget discussions make them uncomfortable** - Deflection, topic changes, discomfort around budget questions
5. **Vague answers about current challenges** - Generic responses, lack of specifics, can't articulate problems
6. **'Need to talk to my boss' responses** - Escalation language, deferred decisions, lack of authority
7. **No current spend on similar solutions** - No existing software budget for this category
8. **'No rush' timeline signals** - Lack of urgency language, no deadline pressure
9. **Deflects all pricing questions** - Avoids pricing specifics, changes subject when price mentioned
10. **No clear pain metrics** - Can't quantify problems, no metrics or KPIs mentioned
11. **Can't name decision maker** - Unclear decision authority, doesn't know who decides
12. **No similar tool spend** - No budget precedent, never bought similar software
13. **No timeline pressure** - No deadline drivers, no urgency indicators
14. **Won't share budget range** - Refuses budget discussion, won't give any budget indication

For each red flag detected, provide:
- The flag name
- Evidence from transcript (quote)
- Confidence level (0.0-1.0)
- Context explaining why this is a red flag

Return a JSON object with this structure:
{
  "red_flags": [
    {
      "flag_name": "Multiple 'committee' decisions",
      "evidence": "Quote from transcript",
      "confidence": 0.85,
      "context": "Explanation of why this is concerning"
    }
  ]
}

Only include red flags that are clearly present in the transcript. Be conservative - false positives are worse than false negatives."""


# Red flag definitions for reference
RED_FLAG_DEFINITIONS = {
    "multiple_committee_decisions": "Multiple 'committee' decisions",
    "spreadsheets_only": "Currently using spreadsheets only",
    "exploring_no_deadline": "'Exploring options' with no deadline",
    "budget_discomfort": "Budget discussions make them uncomfortable",
    "vague_answers": "Vague answers about current challenges",
    "talk_to_boss": "'Need to talk to my boss' responses",
    "no_similar_spend": "No current spend on similar solutions",
    "no_rush": "'No rush' timeline signals",
    "deflects_pricing": "Deflects all pricing questions",
    "no_pain_metrics": "No clear pain metrics",
    "cant_name_decision_maker": "Can't name decision maker",
    "no_tool_spend": "No similar tool spend",
    "no_timeline_pressure": "No timeline pressure",
    "wont_share_budget": "Won't share budget range",
}


class RedFlagDetector:
    """
    Service for detecting red flags in sales meeting transcripts.
    
    Uses OpenAI to analyze transcripts and identify buying intent risks.
    """
    
    def __init__(self):
        """Initialize the red flag detector."""
        api_key = loaded_config.openai_api_key
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables. Red flag detection will fail.")
        self._openai_client = AsyncOpenAI(api_key=api_key) if api_key else None
    
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
    
    async def detect_red_flags(
        self,
        transcript: List[Dict[str, Any]],
        min_confidence: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Detect red flags in a meeting transcript.
        
        Args:
            transcript: List of transcript entries
            min_confidence: Minimum confidence threshold (0.0-1.0)
            
        Returns:
            List of detected red flags with evidence and confidence
        """
        if not transcript:
            return []
        
        transcript_text = self._format_transcript(transcript)
        
        user_prompt = f"""## Meeting Transcript
{transcript_text}

Analyze this transcript and detect any red flags that indicate low buying intent or deal risk. Be specific and cite evidence from the transcript."""
        
        if not self._openai_client:
            logger.error("OpenAI client not initialized - API key missing")
            return []
        
        try:
            response = await self._openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": RED_FLAG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,  # Lower temperature for more consistent detection
                max_tokens=1500,
            )
            
            result = json.loads(response.choices[0].message.content)
            red_flags = result.get("red_flags", [])
            
            # Filter by confidence threshold
            filtered_flags = [
                flag for flag in red_flags
                if flag.get("confidence", 0.0) >= min_confidence
            ]
            
            # Sort by confidence (highest first)
            filtered_flags.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
            
            logger.info(f"Detected {len(filtered_flags)} red flags (min confidence: {min_confidence})")
            return filtered_flags
            
        except Exception as e:
            logger.error(f"Error detecting red flags: {e}")
            return []
    
    def get_red_flag_summary(self, red_flags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of detected red flags.
        
        Args:
            red_flags: List of detected red flags
            
        Returns:
            Summary dictionary with counts and severity
        """
        if not red_flags:
            return {
                "total_flags": 0,
                "high_confidence_flags": 0,
                "severity": "low",
                "summary": "No red flags detected. Deal appears healthy."
            }
        
        high_confidence = [f for f in red_flags if f.get("confidence", 0.0) >= 0.8]
        
        # Determine severity
        if len(red_flags) >= 5 or len(high_confidence) >= 3:
            severity = "high"
        elif len(red_flags) >= 3 or len(high_confidence) >= 2:
            severity = "medium"
        else:
            severity = "low"
        
        return {
            "total_flags": len(red_flags),
            "high_confidence_flags": len(high_confidence),
            "severity": severity,
            "summary": f"Detected {len(red_flags)} red flag(s). {len(high_confidence)} high-confidence flag(s). Deal risk: {severity}."
        }

