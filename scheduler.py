"""Background Task Scheduler for periodic jobs.

Includes:
- Weekly product knowledge scraping from Fynd solution pages
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config.loaded_config import loaded_config

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


async def scrape_product_knowledge():
    """
    Scrape all Fynd product pages and store in database.
    
    This job runs weekly to keep product knowledge fresh.
    """
    logger.info("🔄 Starting scheduled product knowledge scrape...")
    
    try:
        # Import here to avoid circular imports
        from ai_agents.meetings.product_scraper import scrape_all_products, save_to_json
        from database.collection_dao.products import ProductsDao
        
        # Scrape all products
        products = await scrape_all_products()
        
        if not products:
            logger.warning("⚠️ No products scraped - check network or page structure")
            return
        
        # Save to MongoDB
        if hasattr(loaded_config, 'connection_manager') and loaded_config.connection_manager:
            products_dao = ProductsDao(loaded_config.connection_manager.mongo_client)
            count = await products_dao.upsert_many_products(products)
            logger.info(f"✅ Saved {count} products to MongoDB")
        else:
            logger.warning("⚠️ MongoDB not available - saved to JSON only")
        
        # Always save to JSON as fallback
        save_to_json(products)
        
        logger.info(f"✅ Product knowledge scrape completed: {len(products)} products")
        
    except Exception as e:
        logger.error(f"❌ Product knowledge scrape failed: {e}", exc_info=True)


async def check_and_run_initial_scrape():
    """
    Check if initial scrape is needed and run it.
    
    Runs scrape if:
    - No products in database
    - Last scrape was more than 7 days ago
    """
    logger.info("🔍 Checking if initial product scrape is needed...")
    
    try:
        from database.collection_dao.products import ProductsDao
        
        if not hasattr(loaded_config, 'connection_manager') or not loaded_config.connection_manager:
            logger.warning("⚠️ MongoDB not available - running initial scrape anyway")
            await scrape_product_knowledge()
            return
        
        products_dao = ProductsDao(loaded_config.connection_manager.mongo_client)
        
        # Check last scrape time
        last_scrape = await products_dao.get_last_scrape_time()
        
        if last_scrape is None:
            logger.info("📦 No existing products found - running initial scrape")
            await scrape_product_knowledge()
            return
        
        # Check if scrape is older than 7 days
        now = datetime.now(timezone.utc)
        age = now - last_scrape.replace(tzinfo=timezone.utc) if last_scrape.tzinfo is None else now - last_scrape
        
        if age > timedelta(days=7):
            logger.info(f"📦 Last scrape was {age.days} days ago - running refresh scrape")
            await scrape_product_knowledge()
        else:
            logger.info(f"✅ Product knowledge is fresh (last scraped {age.days} days ago)")
            
    except Exception as e:
        logger.error(f"❌ Error checking initial scrape: {e}", exc_info=True)
        # Try to scrape anyway
        await scrape_product_knowledge()


def get_scheduler() -> AsyncIOScheduler:
    """
    Get or create the global scheduler instance.
    
    Returns:
        AsyncIOScheduler instance
    """
    global _scheduler
    
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    
    return _scheduler


async def start_scheduler():
    """
    Start the background task scheduler.
    
    Schedules:
    - Weekly product scraping (Sunday 2 AM UTC)
    - Initial scrape check on startup
    """
    scheduler = get_scheduler()
    
    # Add weekly product scraping job - every Sunday at 2 AM UTC
    scheduler.add_job(
        scrape_product_knowledge,
        CronTrigger(
            day_of_week='sun',
            hour=2,
            minute=0,
            timezone='UTC',
        ),
        id='weekly_product_scrape',
        name='Weekly Product Knowledge Scrape',
        replace_existing=True,
    )
    
    logger.info("📅 Scheduled weekly product scraping job (Sunday 2:00 AM UTC)")
    
    # Start the scheduler
    scheduler.start()
    logger.info("✅ Background scheduler started")
    
    # Run initial scrape check in background (don't block startup)
    asyncio.create_task(check_and_run_initial_scrape())


async def stop_scheduler():
    """Stop the background task scheduler."""
    global _scheduler
    
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("✅ Background scheduler stopped")
    
    _scheduler = None


# Manual trigger functions for admin use

async def trigger_product_scrape():
    """
    Manually trigger a product knowledge scrape.
    
    Can be called from an admin endpoint or CLI.
    """
    logger.info("🔧 Manual product scrape triggered")
    await scrape_product_knowledge()


def get_scheduler_status() -> dict:
    """
    Get current scheduler status.
    
    Returns:
        Dictionary with scheduler info
    """
    scheduler = get_scheduler()
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    
    return {
        "running": scheduler.running if _scheduler else False,
        "jobs": jobs,
    }

