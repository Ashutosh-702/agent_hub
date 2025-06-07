#!/usr/bin/env python3
"""
Model Validation Script

This script validates the data models and their interactions to identify potential issues.
"""

import sys
from typing import List
from loguru import logger

from sdr.models import Company, WorkflowState
from sdr.logging_config import sdr_logger
from sdr.nodes.streamlined_web_enricher import StreamlinedWebEnricher
from sdr.nodes.file_storage import serialize_company_data
from sdr.nodes.company_list_retriever import _normalize_company_data
import pandas as pd


def validate_company_model():
    """Validate the Company model and its attributes"""
    logger.info("Testing Company model creation...")
    
    # Test minimal company creation
    minimal_company = Company(name="Test Company")
    logger.info(f"Created minimal company: {minimal_company}")
    
    # Test full company creation
    full_company = Company(
        name="Full Test Company",
        website="https://example.com",
        domain="example.com",
        industry="Technology",
        size="101-500",
        location="New York, USA",
        description="A test company",
        linkedin_url="https://linkedin.com/company/test"
    )
    logger.info(f"Created full company: {full_company}")
    
    # Test attribute access
    logger.info("Testing attribute access...")
    attributes = [
        'name', 'website', 'domain', 'industry', 
        'size', 'location', 'description', 'linkedin_url'
    ]
    
    for attr in attributes:
        try:
            value = getattr(minimal_company, attr)
            logger.info(f"Minimal company.{attr} = {value}")
        except AttributeError as e:
            logger.error(f"❌ Failed to access minimal_company.{attr}: {e}")
    
    # Test serialization
    logger.info("Testing company serialization...")
    try:
        serialized = serialize_company_data(minimal_company, {"test": "data"})
        logger.info(f"Serialized minimal company: {serialized}")
    except Exception as e:
        logger.error(f"❌ Failed to serialize minimal company: {e}")
    
    try:
        serialized = serialize_company_data(full_company, {"test": "data"})
        logger.info(f"Serialized full company: {serialized}")
    except Exception as e:
        logger.error(f"❌ Failed to serialize full company: {e}")
    
    return minimal_company, full_company


def validate_company_list_retrieval():
    """Validate company list retrieval from different data sources"""
    logger.info("Testing company list retrieval...")
    
    # Test with a minimal DataFrame
    data = {"company": ["Company A", "Company B", "Company C"]}
    df = pd.DataFrame(data)
    
    try:
        companies = _normalize_company_data(df)
        logger.info(f"Created {len(companies)} companies from minimal DataFrame")
        for company in companies:
            logger.info(f"Company: {company}")
    except Exception as e:
        logger.error(f"❌ Failed to normalize minimal DataFrame: {e}")
    
    # Test with a more complex DataFrame
    data = {
        "company_name": ["Company D", "Company E", "Company F"],
        "website": ["http://d.com", "http://e.com", "http://f.com"],
        "industry": ["Tech", "Finance", "Healthcare"]
    }
    df = pd.DataFrame(data)
    
    try:
        companies = _normalize_company_data(df)
        logger.info(f"Created {len(companies)} companies from complex DataFrame")
        for company in companies:
            logger.info(f"Company: {company.name}, Website: {company.website}, Industry: {company.industry}")
    except Exception as e:
        logger.error(f"❌ Failed to normalize complex DataFrame: {e}")
    
    return companies


def validate_web_enricher(companies: List[Company]):
    """Validate web enricher with different company objects"""
    logger.info("Testing web enricher with different company objects...")
    
    # Create dummy config
    config = {
        "openai_api_key": "dummy_key",
        "custom_prompts": {
            "web_enricher_system_prompt": "Test prompt for {company_name} with website {company_website}",
            "web_enricher_user_prompt": "Test user prompt",
            "web_enricher_output_format": "Test output format"
        }
    }
    
    # Test prompt construction with different company objects
    for company in companies:
        try:
            enricher = StreamlinedWebEnricher(config)
            
            # Access the system_prompt formatting directly to test
            # This is a simplified test that doesn't make API calls
            company_website = getattr(company, 'website', None) or 'Unknown - MUST FIND'
            company_industry = getattr(company, 'industry', None) or 'Unknown - MUST DETERMINE'
            company_location = getattr(company, 'location', None) or 'Unknown - MUST FIND'
            
            system_prompt = enricher.prompts.get_prompt(
                "web_enricher_system_prompt",
                company_name=company.name,
                company_website=company_website,
                company_industry=company_industry,
                company_location=company_location
            )
            
            logger.info(f"Generated system prompt for {company.name}: {system_prompt}")
        except Exception as e:
            logger.error(f"❌ Failed to create web enricher for {company.name}: {e}")


def validate_workflow_state():
    """Validate WorkflowState with different company objects"""
    logger.info("Testing WorkflowState...")
    
    # Create minimal and full companies
    minimal_company = Company(name="Minimal State Company")
    full_company = Company(
        name="Full State Company",
        website="https://example.com",
        domain="example.com"
    )
    
    # Create workflow state with required run_directories
    state = WorkflowState(run_directories={
        "run_id": "test_run",
        "run_dir": "output/test_run",
        "results_dir": "output/test_run/results",
        "progress_dir": "output/test_run/progress",
        "logs_dir": "output/test_run/logs",
        "final_dir": "output/test_run/final"
    })
    state.companies = [minimal_company, full_company]
    state.current_company_index = 0
    state.current_company = state.companies[0]
    
    logger.info(f"Created WorkflowState with {len(state.companies)} companies")
    logger.info(f"Current company: {state.current_company.name}")
    
    # Test state transitions
    state.current_company_index += 1
    state.current_company = state.companies[state.current_company_index]
    
    logger.info(f"Transitioned to next company: {state.current_company.name}")
    
    # Test enriched data storage
    state.enriched_data[minimal_company.name] = {
        "test_data": "This is test enriched data",
        "web_search_analysis": {
            "research_summary": {
                "website_found": "https://found-website.com",
                "industry_identified": "Found Industry"
            }
        }
    }
    
    logger.info(f"Added enriched data for {minimal_company.name}")
    logger.info(f"Enriched data: {state.enriched_data.get(minimal_company.name)}")
    
    return state


def main():
    """Main validation function"""
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>")
    
    logger.info("=" * 60)
    logger.info("Starting model validation...")
    logger.info("=" * 60)
    
    # Validate Company model
    minimal_company, full_company = validate_company_model()
    
    # Validate company list retrieval
    companies = validate_company_list_retrieval()
    
    # Validate web enricher
    validate_web_enricher([minimal_company, full_company] + companies)
    
    # Validate workflow state
    state = validate_workflow_state()
    
    logger.info("=" * 60)
    logger.info("Model validation completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main() 