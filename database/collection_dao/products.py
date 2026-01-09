"""Products Collection DAO for product knowledge storage."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from database.base_dao import BaseMongoDao


class ProductsDao(BaseMongoDao):
    """
    Data Access Object for the products collection.
    
    Stores scraped product knowledge from Fynd solution pages,
    used for AI insights during live meetings.
    """
    
    COLLECTION_NAME = "products"
    
    def __init__(self, mongo_client: AsyncIOMotorClient, database_name: str = "linkedin_sdr"):
        """
        Initialize the Products DAO.
        
        Args:
            mongo_client: MongoDB client instance
            database_name: Database name (default: linkedin_sdr)
        """
        super().__init__(mongo_client, self.COLLECTION_NAME, database_name)
    
    async def upsert_product(self, product_id: str, data: Dict[str, Any]) -> bool:
        """
        Insert or update a product.
        
        Args:
            product_id: Unique product identifier (e.g., 'storefront', 'oms')
            data: Product data dictionary
            
        Returns:
            True if successful
        """
        # Ensure product_id is in the data
        data["product_id"] = product_id
        data["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.collection.update_one(
            {"product_id": product_id},
            {
                "$set": data,
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
            },
            upsert=True
        )
        
        return result.acknowledged
    
    async def upsert_many_products(self, products: Dict[str, Dict[str, Any]]) -> int:
        """
        Insert or update multiple products.
        
        Args:
            products: Dictionary mapping product_id to product data
            
        Returns:
            Number of products upserted
        """
        count = 0
        for product_id, data in products.items():
            success = await self.upsert_product(product_id, data)
            if success:
                count += 1
        return count
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single product by ID.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product data or None if not found
        """
        return await self.find_one({"product_id": product_id})
    
    async def get_products_by_ids(self, product_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple products by their IDs.
        
        Args:
            product_ids: List of product identifiers
            
        Returns:
            Dictionary mapping product_id to product data
        """
        cursor = self.collection.find({"product_id": {"$in": product_ids}})
        products = await cursor.to_list(length=None)
        
        return {p["product_id"]: p for p in products}
    
    async def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Get all products.
        
        Returns:
            List of all product documents
        """
        cursor = self.collection.find({})
        return await cursor.to_list(length=None)
    
    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get products by category.
        
        Args:
            category: Product category (e.g., 'Supply Chain', 'Retail')
            
        Returns:
            List of products in the category
        """
        cursor = self.collection.find({"category": category})
        return await cursor.to_list(length=None)
    
    async def get_last_scrape_time(self) -> Optional[datetime]:
        """
        Get the timestamp of the most recent scrape.
        
        Returns:
            Datetime of last scrape or None if no products exist
        """
        # Find the most recently scraped product
        product = await self.collection.find_one(
            {},
            sort=[("scraped_at", -1)],
            projection={"scraped_at": 1}
        )
        
        if product and "scraped_at" in product:
            scraped_at = product["scraped_at"]
            # Handle both string and datetime formats
            if isinstance(scraped_at, str):
                return datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
            return scraped_at
        
        return None
    
    async def get_scrape_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the scraped products.
        
        Returns:
            Dictionary with count, last_scrape_time, categories
        """
        total_count = await self.collection.count_documents({})
        last_scrape = await self.get_last_scrape_time()
        
        # Get distinct categories
        categories = await self.collection.distinct("category")
        
        return {
            "total_products": total_count,
            "last_scrape_time": last_scrape.isoformat() if last_scrape else None,
            "categories": categories,
        }
    
    async def delete_product(self, product_id: str) -> bool:
        """
        Delete a product.
        
        Args:
            product_id: Product identifier
            
        Returns:
            True if deleted
        """
        result = await self.delete_one({"product_id": product_id})
        return result > 0
    
    async def search_products(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search products with optional filters.
        
        Args:
            query: Text search query (searches name, tagline, description)
            category: Filter by category
            limit: Maximum number of results
            
        Returns:
            List of matching products
        """
        filter_query = {}
        
        if category:
            filter_query["category"] = category
        
        if query:
            # Simple text search across key fields
            filter_query["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"tagline": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]
        
        cursor = self.collection.find(filter_query).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_product_for_insights(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product data formatted for the insights engine.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product data with key fields for AI context
        """
        product = await self.get_product(product_id)
        
        if not product:
            return None
        
        # Return only the fields needed for insights
        return {
            "product_id": product.get("product_id"),
            "name": product.get("name"),
            "tagline": product.get("tagline"),
            "description": product.get("description"),
            "key_features": product.get("key_features", []),
            "benefits": product.get("benefits", []),
            "differentiators": product.get("differentiators", []),
            "common_objections": product.get("common_objections", {}),
            "customer_logos": product.get("customer_logos", []),
            "target_industries": product.get("target_industries", []),
            "faq": product.get("faq", []),
        }
    
    async def get_products_for_insights(
        self,
        product_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple products formatted for the insights engine.
        
        Args:
            product_ids: List of product identifiers
            
        Returns:
            Dictionary mapping product_id to insights-ready data
        """
        result = {}
        for product_id in product_ids:
            data = await self.get_product_for_insights(product_id)
            if data:
                result[product_id] = data
        return result

