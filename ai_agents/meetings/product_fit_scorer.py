"""Product-Company Fit Scoring Service."""

import json
import logging
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI

from config.loaded_config import loaded_config

logger = logging.getLogger(__name__)


PRODUCT_FIT_SYSTEM_PROMPT = """You are a sales intelligence analyst. Analyze the meeting transcript to score how well each product fits the company's needs.

For each product, evaluate the fit based on:

1. **Pain Points Alignment** - Do the pain points mentioned match the product's capabilities?
2. **Technical Requirements** - Do their technical needs align with the product's features?
3. **Budget Signals** - Are there positive budget indicators (budget exists, willing to invest)?
4. **Timeline Urgency** - Is there urgency or timeline pressure that indicates real need?
5. **Buying Signals vs Red Flags** - Ratio of positive buying signals to red flags

Score each product on a scale of 0-100 where:
- 90-100: Excellent fit, strong buying signals, high likelihood of close
- 70-89: Good fit, some buying signals, worth pursuing
- 50-69: Moderate fit, mixed signals, needs more qualification
- 30-49: Weak fit, more red flags than signals, low priority
- 0-29: Poor fit, strong red flags, likely not a good match

For each product, provide:
- Score (0-100)
- Reasoning (2-3 sentences explaining the score)
- Key strengths (what aligns well)
- Key concerns (what doesn't align or red flags)

Return a JSON object with this structure:
{
  "product_scores": [
    {
      "product_id": "OMS",
      "product_name": "Fynd OMS",
      "score": 75,
      "reasoning": "Strong alignment with pain points around inventory management, but budget concerns exist.",
      "key_strengths": ["Real-time inventory sync matches their need", "Omnichannel capabilities align"],
      "key_concerns": ["Budget uncertainty", "Timeline not urgent"]
    }
  ]
}

Be honest and objective. Lower scores are valuable if they prevent wasted effort."""


class ProductFitScorer:
    """
    Service for scoring product-company fit based on meeting transcripts.
    
    Analyzes how well each product matches the company's needs, pain points,
    and buying signals from the conversation.
    """
    
    def __init__(self):
        """Initialize the product fit scorer."""
        api_key = loaded_config.openai_api_key
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables. Product scoring will fail.")
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
    
    def _format_product_info(self, product_id: str, product_info: Dict[str, Any]) -> str:
        """Format product information for the prompt."""
        parts = [
            f"**{product_info.get('name', product_id)}**",
            f"Description: {product_info.get('description', 'N/A')}",
        ]
        
        if product_info.get('key_features'):
            parts.append(f"Key Features: {', '.join(product_info['key_features'])}")
        
        if product_info.get('differentiators'):
            parts.append(f"Differentiators: {', '.join(product_info['differentiators'])}")
        
        if product_info.get('ideal_customer_profile'):
            icp = product_info['ideal_customer_profile']
            if icp.get('pain_points'):
                parts.append(f"Target Pain Points: {', '.join(icp['pain_points'])}")
            if icp.get('industries'):
                parts.append(f"Target Industries: {', '.join(icp['industries'])}")
        
        return "\n".join(parts)
    
    def _format_company_context(self, company_data: Optional[Dict[str, Any]] = None) -> str:
        """Format company context for the prompt."""
        if not company_data:
            return "No company data available"
        
        parts = [f"Company: {company_data.get('name', 'Unknown')}"]
        
        if company_data.get('industry'):
            parts.append(f"Industry: {company_data['industry']}")
        
        if company_data.get('enriched_data'):
            enriched = company_data['enriched_data']
            if enriched.get('web_search_analysis', {}).get('research_summary'):
                summary = enriched['web_search_analysis']['research_summary']
                if summary.get('pain_points'):
                    parts.append(f"Inferred Pain Points: {', '.join(summary['pain_points'])}")
        
        return "\n".join(parts)
    
    async def score_products(
        self,
        transcript: List[Dict[str, Any]],
        product_ids: List[str],
        product_info: Dict[str, Dict[str, Any]],
        company_data: Optional[Dict[str, Any]] = None,
        red_flags: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score product-company fit for each product.
        
        Args:
            transcript: List of transcript entries
            product_ids: List of product IDs to score
            product_info: Dictionary mapping product_id to product information
            company_data: Company masterdata
            red_flags: List of detected red flags (optional)
            
        Returns:
            List of product scores with reasoning
        """
        if not transcript or not product_ids:
            return []
        
        transcript_text = self._format_transcript(transcript)
        company_context = self._format_company_context(company_data)
        
        # Format product information
        products_text = []
        for pid in product_ids:
            if pid in product_info:
                products_text.append(self._format_product_info(pid, product_info[pid]))
            else:
                products_text.append(f"**{pid}** - Product information not available")
        
        # Format red flags if provided
        red_flags_text = ""
        if red_flags:
            flags_list = [f"- {f.get('flag_name', 'Unknown')}: {f.get('evidence', '')[:100]}" for f in red_flags]
            red_flags_text = "\n".join(flags_list)
        
        user_prompt = f"""## Company Context
{company_context}

## Products to Score
{chr(10).join(products_text)}

## Meeting Transcript
{transcript_text}

{f'## Red Flags Detected{chr(10)}{red_flags_text}' if red_flags_text else ''}

Score each product's fit with this company based on the transcript. Consider pain points mentioned, technical requirements, budget signals, timeline urgency, and buying signals vs red flags."""
        
        if not self._openai_client:
            logger.error("OpenAI client not initialized - API key missing")
            return [
                {
                    "product_id": pid,
                    "product_name": product_info.get(pid, {}).get("name", pid),
                    "score": 50,
                    "reasoning": "OpenAI API key not configured",
                    "key_strengths": [],
                    "key_concerns": ["API key missing"],
                }
                for pid in product_ids
            ]
        
        try:
            response = await self._openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": PRODUCT_FIT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000,
            )
            
            result = json.loads(response.choices[0].message.content)
            product_scores = result.get("product_scores", [])
            
            # Ensure all products are scored
            scored_ids = {ps.get("product_id") for ps in product_scores}
            for pid in product_ids:
                if pid not in scored_ids:
                    # Add default score for products not in response
                    product_scores.append({
                        "product_id": pid,
                        "product_name": product_info.get(pid, {}).get("name", pid),
                        "score": 50,
                        "reasoning": "Insufficient information in transcript to assess fit.",
                        "key_strengths": [],
                        "key_concerns": ["Limited discussion of this product in the meeting"],
                    })
            
            logger.info(f"Scored {len(product_scores)} products")
            return product_scores
            
        except Exception as e:
            logger.error(f"Error scoring products: {e}")
            # Return default scores on error
            return [
                {
                    "product_id": pid,
                    "product_name": product_info.get(pid, {}).get("name", pid),
                    "score": 50,
                    "reasoning": f"Error scoring product: {str(e)}",
                    "key_strengths": [],
                    "key_concerns": ["Scoring error occurred"],
                }
                for pid in product_ids
            ]

