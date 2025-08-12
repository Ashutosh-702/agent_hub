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
from database.collection_dao.company_mappings import CompanyMappingsDao
from database.collection_dao.campaigns import CampaignsDao
from config.loaded_config import loaded_config
from datetime import datetime
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
        cached_data_db = await companies_dao.get_companies({"location.name":config.get("target", {}).get("location", {}).get("names", []), "location.type": config.get("target", {}).get("location", {}).get("type", ""), "profile.industry":config.get("segmentation", {}).get("industry", [])})
        for company_data in cached_data_db:
            cached_data.append({'id': company_data['identifiers']['source_id'],'name': company_data['identifiers']['name']})
        cached_ids = [company['_id'] for company in cached_data_db]
        lusha_company_data = get_companies_from_lusha(config,cached_data) # List of {'id': int, 'name': str}
        # lusha_company_data = [{'id':1,'name': "Company 1"},{'id':2,'name': "Company 2"},{'id':3,'name': "Company 3"}]
        print(f"Found {len(lusha_company_data)} companies from lusha.")
        print("Fetching companies from core_signal...")
        core_signal_company_data = collect_companies_from_search(config, lusha_company_data+cached_data) # List of {'id': int, 'name': str}
        # core_signal_company_data = [{'id':4,'name': "Company 4"},{'id':5,'name': "Company 5"},{'id':6,'name': "Company 6"}]
        total_company_data = lusha_company_data+core_signal_company_data
        companies_list = []
        if total_company_data:
            for company_data in lusha_company_data:
                company_doc = {
                    "identifiers":{
                        "source_id": company_data["id"],
                        "name": company_data["name"],
                    }, 
                    "profile":{
                        "industry": config.get("segmentation")['industry'],  
                        "revenue_min": config.get("target", "")['revenue_min'],
                        "revenue_max": config.get("target", "")['revenue_max'],
                        "employee_count": config.get("target", "")['employee_count'],
                    },
                    "location":{
                        "type": config.get("target", "")['location']['type'],
                        "name": config.get("target", "")['location']['names'],
                    },
                    "source": "lusha",
                    "metadata":{
                        "created_at":datetime.utcnow(),
                        "updated_at":datetime.utcnow(),
                        "api_response": company_data["api_response_metadata"],
                    }
                }
                companies_list.append(company_doc)
            for company_data in core_signal_company_data:
                company_doc = {
                    "identifiers":{
                        "source_id":company_data["id"],
                        "name": company_data["name"],
                    },
                    "profile":{
                        "industry": config.get("segmentation")['industry'],  
                        "revenue_min": config.get("target", "")['revenue_min'],
                        "revenue_max": config.get("target", "")['revenue_max'],
                        "employee_count": config.get("target", "")['employee_count'],
                    },
                    "location":{
                        "type": config.get("target", "")['location']['type'],
                        "name": config.get("target", "")['location']['names'],
                    },
                    "source": "coresignal",
                    "metadata":{
                        "created_at":datetime.utcnow(),
                        "updated_at":datetime.utcnow(),
                        "api_response": company_data["api_response_metadata"],
                    }
                }
                companies_list.append(company_doc)
            inserted_ids = await companies_dao.create_companies(companies_list)
            print(f"Total new companies added into companies collection: {len(inserted_ids)}")
            id_list = inserted_ids + cached_ids
            company_mappings_dao = CompanyMappingsDao(loaded_config.connection_manager.mongo_client)
            mapping_doc = {
                "references":{
                    "campaign_id": config.get("_id"),
                    "company_ids": id_list,
                    "company_count": len(id_list),
                },
                "snapshot": {
                    "industry": config.get("segmentation")['industry'], 
                    "location": config.get("target", "")['location']['names'],
                    "revenue_min": config.get("target", "")['revenue_min'],
                    "revenue_max": config.get("target", "")['revenue_max'],
                    "employee_count": config.get("target", "")['employee_count'],
                    "keywords": config.get("segmentation", "")['keywords'],
                    "categories": config.get("segmentation", "")['categories'],
                },
            }
            await company_mappings_dao.create_company_mapping(mapping_doc)
            campaigns_dao = CampaignsDao(loaded_config.connection_manager.mongo_client)
            await campaigns_dao.update_campaign_status(mapping_doc['references']['campaign_id'],"processing")
            print(f"Updated status of {mapping_doc['references']['campaign_id']} to 'processing'")
    except Exception as e:
        print(f"Error while processing company search: {str(e)}")
    return {
        "companies": total_company_data+cached_data
    }
if __name__ == '__main__':
    cli()