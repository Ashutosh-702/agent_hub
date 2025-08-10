#!/usr/bin/env python3
"""
Lead Generation CLI Tool

Usage:
    python -m core_sdr cli dsl "give 1 company in Mumbai"
    python -m core_sdr cli health
"""

import json
import logging
import os
import sys
from typing import Dict, Any
import asyncclick as click
from click import Context
from dotenv import load_dotenv
from ai_agents.core_sdr.src.parsers.company_name_uploader import upload_company_name_to_csv,update_history
from ai_agents.core_sdr.src.parsers.dsl_query_processor import SimpleDSLProcessor
from ai_agents.core_sdr.src.api.coresignal_api import collect_companies_from_search
from ai_agents.core_sdr.src.api.lusha_api import lusha_collect_companies_from_search
from ai_agents.core_sdr.src.parsers.lusha_helper import sheets_to_lusha_config,get_companies_from_lusha
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.company_mappings import CompanyMappingsDao
from database.collection_dao.campaigns import CampaignsDao
from config.loaded_config import loaded_config
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
    try:
        companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
        print("Fetching companies from lusha...")
        lusha_company_data = get_companies_from_lusha(config) # List of {'id': int, 'name': str}
        print(f"Found {len(lusha_company_data)} companies from lusha.")
        print("Fetching companies from core_signal...")
        core_signal_company_data = collect_companies_from_search(config, lusha_company_data) # List of {'id': int, 'name': str}
        total_company_data = lusha_company_data+core_signal_company_data
        companies_list = []
        if total_company_data:
            for company_data in lusha_company_data:
                company_doc = {
                    "company_id":company_data["id"],
                    "name": company_data["name"],
                    "industry": config.get("industry"),  
                    "revenue_min": config.get("revenue_min", ""),
                    "revenue_max": config.get("revenue_max", ""),
                    "employee_count": config.get("employee_count", ""),
                    "location": config.get("location", ""),
                    "location_type": config.get("location_type", ""),
                    "source": "lusha"
                }
                companies_list.append(company_doc)
            for company_data in core_signal_company_data:
                company_doc = {
                    "company_id":company_data["id"],
                    "name": company_data["name"],
                    "industry": config.get("industry"), 
                    "revenue_min": config.get("revenue_min", ""),
                    "revenue_max": config.get("revenue_max", ""),
                    "employee_count": config.get("employee_count", ""),
                    "location": config.get("location", ""),
                    "location_type": config.get("location_type", ""),
                    "source": "coresignal"
                }
                companies_list.append(company_doc)
            inserted_ids = await companies_dao.create_companies(companies_list)
            print(f"Total companies added into companies collection: {len(inserted_ids)}")

            company_mappings_dao = CompanyMappingsDao(loaded_config.connection_manager.mongo_client)
            mapping_doc = {
                "campaign_id":config.get("campaign_id",""),
                "campaign_data": {
                    "industry": config.get("industry"),
                    "location": config.get("location", ""),
                    "employee_count": config.get("employee_count", ""),
                    "revenue_min": config.get("revenue_min", ""),
                    "revenue_max": config.get("revenue_max", ""),
                    "keywords": config.get("keywords", ""),
                    "categories": config.get("categories", "")
                },
                "company_ids": inserted_ids,
                "company_count": len(inserted_ids)
            }
            await company_mappings_dao.create_company_mapping(mapping_doc)
            campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
            await campaigns_dao.update_campaign_status(mapping_doc['campaign_id'],"processing")
            print(f"Updated status of {mapping_doc['campaign_id']} to 'processing'")
    except Exception as e:
        print(f"Error while processing company search: {str(e)}")
    return {
        "companies": total_company_data
    }
if __name__ == '__main__':
    cli()