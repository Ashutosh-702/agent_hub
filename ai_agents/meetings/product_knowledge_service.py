"""Product Knowledge Service for loading and querying product information."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ProductKnowledgeService:
    """
    Service for loading and querying product knowledge.
    
    Loads product information from JSON config and provides methods
    to match products to company pain points and generate context.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the product knowledge service.
        
        Args:
            config_path: Path to product_knowledge.json file. If None, uses default location.
        """
        if config_path is None:
            # Default to config directory relative to this file
            current_dir = Path(__file__).parent
            config_path = current_dir / "config" / "product_knowledge.json"
        
        self.config_path = Path(config_path)
        self._product_info: Dict[str, Dict[str, Any]] = {}
        self._load_product_info()
    
    def _load_product_info(self):
        """Load product information from JSON config file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Product knowledge config not found at {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._product_info = json.load(f)
            
            logger.info(f"Loaded product knowledge for {len(self._product_info)} products")
        except Exception as e:
            logger.error(f"Error loading product knowledge: {e}")
            self._product_info = {}
    
    def get_product_info(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information for a specific product.
        
        Args:
            product_id: Product ID (e.g., "OMS", "WMS")
            
        Returns:
            Product information dictionary or None if not found
        """
        return self._product_info.get(product_id)
    
    def get_all_products(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all product information.
        
        Returns:
            Dictionary mapping product_id to product info
        """
        return self._product_info.copy()
    
    def get_products_by_ids(self, product_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get information for multiple products.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            Dictionary mapping product_id to product info (only includes found products)
        """
        return {
            pid: info
            for pid in product_ids
            if (info := self._product_info.get(pid)) is not None
        }
    
    def match_products_to_pain_points(
        self,
        pain_points: List[str],
        industry: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Match products to company pain points.
        
        Args:
            pain_points: List of pain points mentioned
            industry: Company industry (optional)
            
        Returns:
            List of products with match scores, sorted by relevance
        """
        if not pain_points:
            return []
        
        # Normalize pain points to lowercase for matching
        pain_points_lower = [pp.lower() for pp in pain_points]
        
        matches = []
        for product_id, product_info in self._product_info.items():
            score = 0
            matched_pain_points = []
            
            # Check ideal customer profile pain points
            icp = product_info.get("ideal_customer_profile", {})
            icp_pain_points = icp.get("pain_points", [])
            
            for icp_pp in icp_pain_points:
                icp_pp_lower = icp_pp.lower()
                # Check if any mentioned pain point matches
                for mentioned_pp in pain_points_lower:
                    # Simple keyword matching (can be enhanced with semantic search)
                    if any(keyword in mentioned_pp for keyword in icp_pp_lower.split()):
                        score += 2
                        matched_pain_points.append(icp_pp)
                        break
            
            # Check industry match
            if industry:
                icp_industries = icp.get("industries", [])
                if industry.lower() in [ind.lower() for ind in icp_industries]:
                    score += 1
            
            if score > 0:
                matches.append({
                    "product_id": product_id,
                    "product_name": product_info.get("name", product_id),
                    "match_score": score,
                    "matched_pain_points": matched_pain_points,
                    "product_info": product_info,
                })
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
    
    def get_product_context_for_ai(
        self,
        product_ids: List[str],
        include_competitors: bool = True,
    ) -> str:
        """
        Format product information for AI prompts.
        
        Args:
            product_ids: List of product IDs to include
            include_competitors: Whether to include competitor information
            
        Returns:
            Formatted string with product information
        """
        products = self.get_products_by_ids(product_ids)
        if not products:
            return "No product information available"
        
        parts = []
        for product_id, product_info in products.items():
            product_text = f"**{product_info.get('name', product_id)}**\n"
            product_text += f"Tagline: {product_info.get('tagline', 'N/A')}\n"
            product_text += f"Description: {product_info.get('description', 'N/A')}\n"
            
            if product_info.get('key_features'):
                product_text += f"Key Features: {', '.join(product_info['key_features'])}\n"
            
            if product_info.get('differentiators'):
                product_text += f"Differentiators: {', '.join(product_info['differentiators'])}\n"
            
            icp = product_info.get('ideal_customer_profile', {})
            if icp.get('pain_points'):
                product_text += f"Target Pain Points: {', '.join(icp['pain_points'])}\n"
            
            if include_competitors and product_info.get('competitors'):
                product_text += "\nCompetitors:\n"
                for comp_name, comp_info in product_info['competitors'].items():
                    product_text += f"- {comp_name}: {comp_info.get('their_strength', 'N/A')}\n"
                    product_text += f"  Our Advantage: {comp_info.get('our_advantage', 'N/A')}\n"
            
            parts.append(product_text)
        
        return "\n\n".join(parts)
    
    def get_competitive_positioning(
        self,
        product_id: str,
        competitor_name: str,
    ) -> Optional[Dict[str, str]]:
        """
        Get competitive positioning for a product against a specific competitor.
        
        Args:
            product_id: Product ID
            competitor_name: Competitor name
            
        Returns:
            Dictionary with their_strength and our_advantage, or None if not found
        """
        product_info = self.get_product_info(product_id)
        if not product_info:
            return None
        
        competitors = product_info.get("competitors", {})
        return competitors.get(competitor_name)
    
    def get_objection_handlers(
        self,
        product_id: str,
    ) -> Dict[str, str]:
        """
        Get common objection handlers for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            Dictionary mapping objection to response
        """
        product_info = self.get_product_info(product_id)
        if not product_info:
            return {}
        
        return product_info.get("common_objections", {})


