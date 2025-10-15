#!/usr/bin/env python3
"""
Lead Generation CLI Tool

Usage:
    python -m core_sdr cli dsl "give 1 company in Mumbai"
    python -m core_sdr cli health
"""

import logging
import os
import sys
from typing import Dict, Any
import asyncclick as click
from click import Context
from dotenv import load_dotenv
from ai_agents.core_sdr.src.api.coresignal_api import collect_companies_from_search
from ai_agents.core_sdr.src.parsers.lusha_helper import get_companies_from_lusha
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.campaign_company_runs import CampaignCompanyRunsDao
from database.collection_dao.campaigns import CampaignsDao
from config.loaded_config import loaded_config
from datetime import datetime
from ai_agents.core_sdr.src.api.company_relevance_check import CompanyRelevanceCheck
from integrations.lusha.lusha_helper import LushaHelper
load_dotenv()
logger = logging.getLogger(__name__)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx: Context, verbose):
    """Lead Generation CLI Tool"""
    ctx.ensure_object(dict)
    
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@cli.command()
@click.argument('query', required=False)
@click.pass_context
async def dsl(ctx, query):
    """Generate Elasticsearch DSL query from natural language."""
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        click.echo("Error: OPENAI_API_KEY environment variable not set", err=True)
        sys.exit(1)
    if not query:
        click.echo("Error: Query is required for DSL generation", err=True)
        return
    
    try:
        click.echo(f"Generating DSL for: {query}")
        click.echo("Core SDR running successfully")
        results = await process_company_search(query)
        click.echo(f"Found {len(results['companies'])} companies")
        click.echo(f"Results saved to: {results['csv_path']}")
    except Exception as e:
        click.echo(f"Processing error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health status."""
    try:
        # Simple health check without orchestrator
        openai_key = os.getenv('OPENAI_API_KEY')
        coresignal_key = os.getenv('CORESIGNAL_API_KEY')
        
        status = "healthy" if openai_key and coresignal_key else "unhealthy"
        
        click.echo(f"System Status: ", nl=False)
        status_color = 'green' if status == 'healthy' else 'red'
        click.secho(status.upper(), fg=status_color)
        
        click.echo("\nComponent Status:")
        
        openai_status = "configured" if openai_key else "missing"
        color = 'green' if openai_status == 'configured' else 'red'
        click.echo(f"  OpenAI API: ", nl=False)
        click.secho(openai_status, fg=color)
        
        coresignal_status = "configured" if coresignal_key else "missing"
        color = 'green' if coresignal_status == 'configured' else 'red'
        click.echo(f"  CoreSignal API: ", nl=False)
        click.secho(coresignal_status, fg=color)
        
    except Exception as e:
        click.echo(f"Health check error: {str(e)}", err=True)
        sys.exit(1)


async def process_company_search(config: Dict[str,Any]) -> Dict[str, Any]:
    """Core function to process company search"""
    # Initialize variables before try block to avoid UnboundLocalError
    total_company_data = []
    cached_data = []
    
    try:
        # Check if connection manager is properly initialized
        if not loaded_config.connection_manager or not loaded_config.connection_manager.mongo_client:
            print("❌ Error: Database connection not initialized")
            return {
                "companies": [],
                "error": "Database connection not available"
            }
            
        companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        print("Fetching companies from lusha...")
        temp_cached_data = []
        # inserted_count = await get_companies_from_lusha(config,temp_cached_data) # List of {'id': int, 'name': str}
        lusha_helper = LushaHelper()
        inserted_count = await lusha_helper.get_companies_from_lusha(config)
        print(f"Found {inserted_count} companies from lusha.")
        print("Fetching companies from core_signal...")
        # core_signal_company_data = collect_companies_from_search(config, cached_data) # List of {'id': int, 'name': str}
        total_company_data = inserted_count
        
        campaign_id = config.get('_id')
        print(f"Total new companies added into companies collection: {inserted_count}")

        campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
        relevance_check = CompanyRelevanceCheck(config)
        await relevance_check.company_relevance_check(campaign_id)
        await campaigns_dao.update_campaign_status(campaign_id,"pending")
        print(f"Updated status of {campaign_id} to 'pending'")
    except Exception as e:
        print(f"Error while processing company search: {str(e)}")
    return {
        "companies": total_company_data
    }
if __name__ == '__main__':
    cli()