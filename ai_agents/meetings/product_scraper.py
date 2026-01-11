"""Product Knowledge Scraper for Fynd Solutions.

Scrapes all Fynd solution pages to extract comprehensive product knowledge
for use in AI-powered sales insights during live meetings.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# All Fynd solutions to scrape
FYND_PRODUCTS = {
    "storefront": {
        "name": "Fynd Storefront",
        "url": "https://www.fynd.com/solutions/storefront",
        "category": "Build Website",
        "subcategory": "E-commerce",
    },
    "fynd_quick": {
        "name": "Fynd Quick Commerce",
        "url": "https://www.fynd.com/solutions/fynd-quick",
        "category": "Build Website",
        "subcategory": "Quick Commerce",
    },
    "b2b_commerce": {
        "name": "Fynd B2B Commerce",
        "url": "https://www.fynd.com/solutions/b2b-commerce",
        "category": "Build Website",
        "subcategory": "B2B",
    },
    "konnect": {
        "name": "Fynd Konnect",
        "url": "https://www.fynd.com/solutions/konnect-integrations",
        "category": "Marketplace",
        "subcategory": "Integrations",
    },
    "ai_pim": {
        "name": "Fynd AI PIM",
        "url": "https://www.fynd.com/solutions/ai-pim",
        "category": "AI Tools",
        "subcategory": "Catalog Management",
    },
    "oms": {
        "name": "Fynd OMS",
        "url": "https://www.fynd.com/solutions/order-management-system",
        "category": "Supply Chain",
        "subcategory": "Order Management",
    },
    "wms": {
        "name": "Fynd WMS",
        "url": "https://www.fynd.com/solutions/wms",
        "category": "Supply Chain",
        "subcategory": "Warehouse Management",
    },
    "tms": {
        "name": "Fynd TMS",
        "url": "https://www.fynd.com/solutions/transport-management-system",
        "category": "Supply Chain",
        "subcategory": "Transport Management",
    },
    "logistics": {
        "name": "Fynd Managed Logistics",
        "url": "https://www.fynd.com/solutions/logistics",
        "category": "Supply Chain",
        "subcategory": "Logistics",
    },
    "pos": {
        "name": "Fynd POS",
        "url": "https://www.fynd.com/solutions/pos",
        "category": "Retail",
        "subcategory": "Point of Sale",
    },
    "kiosk": {
        "name": "Fynd Self-Checkout Kiosk",
        "url": "https://www.fynd.com/solutions/self-checkout-kiosk",
        "category": "Retail",
        "subcategory": "Self-Checkout",
    },
    "scan_and_go": {
        "name": "Fynd Scan & Go",
        "url": "https://www.fynd.com/solutions/self-checkout",
        "category": "Retail",
        "subcategory": "Mobile Checkout",
    },
    "engage": {
        "name": "Fynd Engage",
        "url": "https://www.fynd.com/solutions/engage",
        "category": "Retail",
        "subcategory": "Loyalty & Engagement",
    },
    "endless_aisle": {
        "name": "Fynd Endless Aisle",
        "url": "https://www.fynd.com/solutions/endless-aisle",
        "category": "Retail",
        "subcategory": "Inventory Visibility",
    },
    "clienteling": {
        "name": "Fynd Clienteling",
        "url": "https://www.fynd.com/solutions/clienteling",
        "category": "Retail",
        "subcategory": "Personalization",
    },
    "create": {
        "name": "Fynd Create",
        "url": "https://www.fynd.com/solutions/create",
        "category": "Manufacturing",
        "subcategory": "AI Fashion Design",
    },
    "ai_snap": {
        "name": "Fynd AI Snap",
        "url": "https://www.fynd.com/solutions/ai-snap",
        "category": "AI Tools",
        "subcategory": "AI Photography",
    },
    "pixelbin": {
        "name": "Pixelbin",
        "url": "https://www.fynd.com/solutions/ai-editing-for-commerce",
        "category": "AI Tools",
        "subcategory": "Image Transformation",
    },
    "boltic": {
        "name": "Boltic",
        "url": "https://www.fynd.com/solutions/workflow-automation",
        "category": "AI Tools",
        "subcategory": "Workflow Automation",
    },
    "glamar": {
        "name": "GlamAR",
        "url": "https://www.fynd.com/solutions/3d-ar-vr-try-ons",
        "category": "AI Tools",
        "subcategory": "AR/VR Shopping",
    },
    "kaily": {
        "name": "Kaily",
        "url": "https://www.fynd.com/solutions/ai-agent-builder",
        "category": "AI Tools",
        "subcategory": "AI Agents",
    },
    "partner_program": {
        "name": "Fynd Partner Program",
        "url": "https://partners.fynd.com/",
        "category": "Partner",
        "subcategory": "Partnership",
    },
}


class FyndProductScraper:
    """
    Scraper for Fynd solution pages.
    
    Extracts structured product knowledge including:
    - Product name and tagline
    - Key features with descriptions
    - Benefits and use cases
    - Target industries
    - Customer logos and case studies
    - FAQ/common objections
    - Differentiators
    """
    
    def __init__(self, timeout: float = 30.0):
        """
        Initialize the scraper.
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            follow_redirects=True,
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def _extract_hero_section(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract hero section content (tagline, description)."""
        result = {"tagline": "", "description": ""}
        
        # Try to find h1 or main heading
        h1 = soup.find('h1')
        if h1:
            result["tagline"] = self._clean_text(h1.get_text())
        
        # Try to find description in hero section
        hero_selectors = [
            'section.hero p',
            '.hero-section p',
            'header p',
            '.hero p',
            'h1 + p',
            '.hero-description',
            '[class*="hero"] p',
        ]
        
        for selector in hero_selectors:
            desc = soup.select_one(selector)
            if desc:
                result["description"] = self._clean_text(desc.get_text())
                break
        
        # Fallback: find first substantial paragraph
        if not result["description"]:
            for p in soup.find_all('p'):
                text = self._clean_text(p.get_text())
                if len(text) > 50:
                    result["description"] = text
                    break
        
        return result
    
    def _extract_features(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract key features from the page."""
        features = []
        
        # Look for feature cards or sections
        feature_selectors = [
            '.feature-card',
            '.feature-item',
            '[class*="feature"]',
            '.card',
            '.benefit',
            '[class*="benefit"]',
        ]
        
        for selector in feature_selectors:
            cards = soup.select(selector)
            for card in cards[:10]:  # Limit to 10 features
                title_elem = card.find(['h2', 'h3', 'h4', 'strong'])
                desc_elem = card.find('p')
                
                if title_elem:
                    title = self._clean_text(title_elem.get_text())
                    description = self._clean_text(desc_elem.get_text()) if desc_elem else ""
                    
                    if title and len(title) < 100:  # Filter out long text that's not titles
                        features.append({
                            "title": title,
                            "description": description[:300],  # Limit description length
                        })
        
        # Deduplicate features
        seen = set()
        unique_features = []
        for f in features:
            if f["title"] not in seen:
                seen.add(f["title"])
                unique_features.append(f)
        
        return unique_features[:10]  # Return top 10 unique features
    
    def _extract_benefits(self, soup: BeautifulSoup) -> List[str]:
        """Extract benefits/value propositions."""
        benefits = []
        
        # Look for bullet points in feature/benefit sections
        benefit_selectors = [
            'ul li',
            '.benefits li',
            '[class*="benefit"] li',
            '.feature-list li',
        ]
        
        for selector in benefit_selectors:
            items = soup.select(selector)
            for item in items[:15]:
                text = self._clean_text(item.get_text())
                if 20 < len(text) < 200:  # Filter reasonable length items
                    benefits.append(text)
        
        # Deduplicate
        return list(dict.fromkeys(benefits))[:10]
    
    def _extract_customer_logos(self, soup: BeautifulSoup) -> List[str]:
        """Extract customer/brand logos."""
        logos = []
        
        # Look for logo sections
        logo_selectors = [
            '[class*="logo"] img',
            '[class*="brand"] img',
            '[class*="customer"] img',
            '[class*="partner"] img',
            '.client-logos img',
        ]
        
        for selector in logo_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                alt = img.get('alt', '')
                if alt and len(alt) < 50:
                    logos.append(alt)
        
        # Also look for brand names in text
        brand_section = soup.find(string=re.compile(r'brands|customers|trusted by', re.I))
        if brand_section:
            parent = brand_section.find_parent(['section', 'div'])
            if parent:
                for text in parent.stripped_strings:
                    if len(text) < 30 and text not in ['Brands', 'Customers', 'Trusted by']:
                        logos.append(text)
        
        return list(dict.fromkeys(logos))[:15]
    
    def _extract_faq(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract FAQ items (useful for objection handling)."""
        faqs = []
        
        # Look for FAQ sections
        faq_section = soup.find(string=re.compile(r'FAQ|frequently asked', re.I))
        if faq_section:
            parent = faq_section.find_parent(['section', 'div'])
            if parent:
                # Look for question-answer pairs
                questions = parent.find_all(['h3', 'h4', 'button', '.question'])
                for q in questions[:10]:
                    question = self._clean_text(q.get_text())
                    if '?' in question or question.startswith(('What', 'How', 'Can', 'Is', 'Why')):
                        # Find the answer
                        answer_elem = q.find_next(['p', 'div'])
                        answer = self._clean_text(answer_elem.get_text()) if answer_elem else ""
                        if answer and len(answer) > 20:
                            faqs.append({
                                "question": question,
                                "answer": answer[:500],
                            })
        
        return faqs[:10]
    
    def _extract_differentiators(self, soup: BeautifulSoup) -> List[str]:
        """Extract unique selling points/differentiators."""
        differentiators = []
        
        # Look for "why choose" or "why us" sections
        why_section = soup.find(string=re.compile(r'why choose|why brands|why us|advantages', re.I))
        if why_section:
            parent = why_section.find_parent(['section', 'div'])
            if parent:
                for li in parent.find_all('li'):
                    text = self._clean_text(li.get_text())
                    if 20 < len(text) < 200:
                        differentiators.append(text)
        
        return list(dict.fromkeys(differentiators))[:8]
    
    def _extract_target_industries(self, soup: BeautifulSoup) -> List[str]:
        """Extract target industries from page content."""
        industries = []
        
        # Common industry keywords to look for
        industry_keywords = [
            'retail', 'fashion', 'electronics', 'beauty', 'cosmetics',
            'furniture', 'home decor', 'grocery', 'pharma', 'automotive',
            'sports', 'lifestyle', 'luxury', 'apparel', 'd2c', 'b2b',
            'ecommerce', 'e-commerce', 'quick commerce', 'hyperlocal',
            'manufacturing', 'fmcg', 'consumer goods',
        ]
        
        page_text = soup.get_text().lower()
        
        for industry in industry_keywords:
            if industry in page_text:
                industries.append(industry.title())
        
        return industries[:10]
    
    async def scrape_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single product page.
        
        Args:
            product_id: Product identifier from FYND_PRODUCTS
            
        Returns:
            Structured product data or None if scraping fails
        """
        if product_id not in FYND_PRODUCTS:
            logger.error(f"Unknown product ID: {product_id}")
            return None
        
        product_config = FYND_PRODUCTS[product_id]
        url = product_config["url"]
        
        logger.info(f"Scraping {product_config['name']} from {url}")
        
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all sections
            hero = self._extract_hero_section(soup)
            features = self._extract_features(soup)
            benefits = self._extract_benefits(soup)
            customer_logos = self._extract_customer_logos(soup)
            faq = self._extract_faq(soup)
            differentiators = self._extract_differentiators(soup)
            target_industries = self._extract_target_industries(soup)
            
            # Build structured product data
            product_data = {
                "product_id": product_id,
                "name": product_config["name"],
                "url": url,
                "category": product_config["category"],
                "subcategory": product_config.get("subcategory", ""),
                "tagline": hero["tagline"],
                "description": hero["description"],
                "key_features": features,
                "benefits": benefits,
                "target_industries": target_industries,
                "customer_logos": customer_logos,
                "case_studies": [],  # Could be enhanced with deeper scraping
                "differentiators": differentiators,
                "faq": faq,
                "common_objections": self._derive_objections_from_faq(faq),
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
            
            logger.info(f"Successfully scraped {product_config['name']}: "
                       f"{len(features)} features, {len(benefits)} benefits")
            
            return product_data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def _derive_objections_from_faq(self, faq: List[Dict[str, str]]) -> Dict[str, str]:
        """Convert FAQ items to objection handlers."""
        objections = {}
        for item in faq:
            # Check if it's a common objection pattern
            q = item["question"].lower()
            if any(kw in q for kw in ['cost', 'price', 'much', 'expensive', 'free', 'trial']):
                objections["pricing"] = item["answer"]
            elif any(kw in q for kw in ['integrate', 'integration', 'connect', 'work with']):
                objections["integration"] = item["answer"]
            elif any(kw in q for kw in ['customize', 'customization', 'flexible']):
                objections["customization"] = item["answer"]
            elif any(kw in q for kw in ['support', 'help', 'assistance']):
                objections["support"] = item["answer"]
            elif any(kw in q for kw in ['migrate', 'migration', 'switch', 'move']):
                objections["migration"] = item["answer"]
        return objections
    
    async def scrape_all_products(self) -> Dict[str, Dict[str, Any]]:
        """
        Scrape all Fynd product pages.
        
        Returns:
            Dictionary mapping product_id to product data
        """
        results = {}
        
        # Scrape products with concurrency limit
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def scrape_with_limit(product_id: str):
            async with semaphore:
                await asyncio.sleep(1)  # Be nice to the server
                return product_id, await self.scrape_product(product_id)
        
        tasks = [scrape_with_limit(pid) for pid in FYND_PRODUCTS.keys()]
        
        for coro in asyncio.as_completed(tasks):
            product_id, data = await coro
            if data:
                results[product_id] = data
            else:
                logger.warning(f"Failed to scrape product: {product_id}")
        
        logger.info(f"Scraped {len(results)}/{len(FYND_PRODUCTS)} products successfully")
        return results


def _convert_datetime_to_str(obj: Any) -> Any:
    """
    Recursively convert datetime objects to ISO format strings.
    
    Args:
        obj: Object that may contain datetime objects
        
    Returns:
        Object with datetime objects converted to strings
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _convert_datetime_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_datetime_to_str(item) for item in obj]
    else:
        return obj


def save_to_json(products: Dict[str, Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Save scraped product data to JSON file.
    
    Args:
        products: Dictionary of product data
        output_path: Path to save JSON file. Defaults to config/product_knowledge_scraped.json
    """
    if output_path is None:
        output_path = Path(__file__).parent / "config" / "product_knowledge_scraped.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert datetime objects to strings for JSON serialization
    products_serializable = _convert_datetime_to_str(products)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(products_serializable, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(products)} products to {output_path}")


async def scrape_all_products() -> Dict[str, Dict[str, Any]]:
    """
    Main function to scrape all Fynd products.
    
    Returns:
        Dictionary of scraped product data
    """
    async with FyndProductScraper() as scraper:
        products = await scraper.scrape_all_products()
        
        # Save to JSON as fallback
        save_to_json(products)
        
        return products


# For direct execution / testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        products = await scrape_all_products()
        print(f"\nScraped {len(products)} products:")
        for pid, data in products.items():
            print(f"  - {data['name']}: {len(data['key_features'])} features, "
                  f"{len(data['benefits'])} benefits")
    
    asyncio.run(main())

