"""Context Generation Service for live meeting context and post-call summaries."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI

from config.loaded_config import loaded_config

logger = logging.getLogger(__name__)


MEETING_CONTEXT_PROMPT = """You are an AI sales assistant helping prepare a salesperson for a live client call.

Based on the company information, contact details, and products to discuss, generate a comprehensive meeting context that will help during the call.

Generate a JSON response with this structure:
{
  "company": {
    "name": "company name",
    "industry": "industry type",
    "size": "company size (employees/revenue if available)",
    "website": "company website"
  },
  "contacts": [
    {"name": "full name", "title": "job title"}
  ],
  "products": ["product 1", "product 2"],
  "painPoints": ["likely pain point 1", "likely pain point 2"],
  "previousMeetings": 0,
  "dealStage": "Discovery/Qualification/Demo/Negotiation/Closing"
}

Be specific and use the actual data provided. For pain points, infer likely challenges based on the company's industry, size, and the products being discussed."""


POST_CALL_SUMMARY_PROMPT = """You are an AI sales assistant analyzing a completed sales call.

Based on the meeting transcript and context, generate a comprehensive post-call summary that helps the salesperson with follow-up actions.

Generate a JSON response with this structure:
{
  "summary": "A 2-3 paragraph executive summary of the call, highlighting key outcomes and overall sentiment",
  "keyPoints": ["key discussion point 1", "key discussion point 2", "..."],
  "objections": [
    {"objection": "objection raised", "resolution": "how it was addressed or if left open"}
  ],
  "actionItems": [
    {"item": "action item description", "owner": "who should do it", "dueDate": "suggested due date"}
  ],
  "nextSteps": ["next step 1", "next step 2", "..."],
  "followUpMessages": [
    {
      "contact": "contact name",
      "email": "contact email if available",
      "subject": "suggested email subject",
      "draft": "draft follow-up email message"
    }
  ]
}

Be specific and actionable. Extract real information from the transcript."""


class ContextGenerator:
    """
    Service for generating meeting context and summaries using OpenAI.
    """
    
    def __init__(self):
        """Initialize the context generator."""
        self._client: Optional[AsyncOpenAI] = None
    
    def _get_client(self) -> AsyncOpenAI:
        """Get or create the OpenAI client."""
        if not self._client:
            api_key = loaded_config.openai_api_key
            if not api_key:
                raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
            self._client = AsyncOpenAI(api_key=api_key)
        return self._client
    
    async def generate_meeting_context(
        self,
        company_data: Optional[Dict[str, Any]] = None,
        contacts_data: Optional[List[Dict[str, Any]]] = None,
        products: Optional[List[str]] = None,
        previous_meetings: int = 0,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate meeting context for a live call.
        
        Args:
            company_data: Company information from database
            contacts_data: List of contact information
            products: List of product IDs/names to discuss
            previous_meetings: Number of previous meetings
            notes: Any additional notes
            
        Returns:
            Meeting context dictionary
        """
        try:
            client = self._get_client()
            
            # Build the context prompt
            context_info = []
            
            if company_data:
                context_info.append(f"Company: {json.dumps(company_data, indent=2)}")
            
            if contacts_data:
                context_info.append(f"Contacts: {json.dumps(contacts_data, indent=2)}")
            
            if products:
                context_info.append(f"Products to discuss: {', '.join(products)}")
            
            context_info.append(f"Previous meetings: {previous_meetings}")
            
            if notes:
                context_info.append(f"Meeting notes: {notes}")
            
            user_message = "\n\n".join(context_info) if context_info else "No specific context provided."
            
            logger.info(f"Generating meeting context with OpenAI...")
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": MEETING_CONTEXT_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            context = json.loads(content)
            
            logger.info(f"Meeting context generated successfully")
            return context
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return self._get_fallback_context(company_data, contacts_data, products)
        except Exception as e:
            logger.error(f"Error generating meeting context: {e}")
            return self._get_fallback_context(company_data, contacts_data, products)
    
    async def generate_post_call_summary(
        self,
        transcript: List[Dict[str, Any]],
        company_name: str = "",
        contacts: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        meeting_duration: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a post-call summary from the meeting transcript.
        
        Args:
            transcript: List of transcript entries with speaker, text, timestamp
            company_name: Name of the company
            contacts: List of contact names
            products: List of products discussed
            meeting_duration: Duration in seconds
            
        Returns:
            Post-call summary dictionary
        """
        try:
            client = self._get_client()
            
            # Format transcript for the prompt
            transcript_text = "\n".join([
                f"[{entry.get('speaker', 'Unknown')}] {entry.get('text', '')}"
                for entry in transcript
            ])
            
            # Build context
            context_parts = [
                f"Company: {company_name}" if company_name else "",
                f"Attendees: {', '.join(contacts)}" if contacts else "",
                f"Products: {', '.join(products)}" if products else "",
                f"Duration: {meeting_duration // 60} minutes" if meeting_duration > 0 else "",
            ]
            context = "\n".join([p for p in context_parts if p])
            
            user_message = f"""Meeting Context:
{context}

Meeting Transcript:
{transcript_text}"""
            
            logger.info(f"Generating post-call summary with OpenAI...")
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": POST_CALL_SUMMARY_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            summary = json.loads(content)
            
            logger.info(f"Post-call summary generated successfully")
            return summary
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return self._get_fallback_summary()
        except Exception as e:
            logger.error(f"Error generating post-call summary: {e}")
            return self._get_fallback_summary()
    
    def _get_fallback_context(
        self,
        company_data: Optional[Dict[str, Any]] = None,
        contacts_data: Optional[List[Dict[str, Any]]] = None,
        products: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate fallback context when OpenAI is unavailable."""
        company = {
            "name": company_data.get("name", "Unknown Company") if company_data else "Unknown Company",
            "industry": company_data.get("industry", "Unknown") if company_data else "Unknown",
            "size": company_data.get("size", "Unknown") if company_data else "Unknown",
            "website": company_data.get("website", "") if company_data else "",
        }
        
        contacts = []
        if contacts_data:
            for c in contacts_data:
                name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() or c.get('name', 'Unknown')
                contacts.append({
                    "name": name,
                    "title": c.get("jobTitle", c.get("title", ""))
                })
        
        return {
            "company": company,
            "contacts": contacts,
            "products": products or [],
            "painPoints": [],
            "previousMeetings": 0,
            "dealStage": "Discovery",
        }
    
    def _get_fallback_summary(self) -> Dict[str, Any]:
        """Generate fallback summary when OpenAI is unavailable."""
        return {
            "summary": "Meeting summary could not be generated. Please review the transcript manually.",
            "keyPoints": [],
            "objections": [],
            "actionItems": [],
            "nextSteps": [],
            "followUpMessages": [],
        }


# Singleton instance
context_generator = ContextGenerator()


