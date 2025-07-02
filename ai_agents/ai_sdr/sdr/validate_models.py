#!/usr/bin/env python3
"""
Model Validation Script

This script validates the data models and their interactions to identify potential issues.
"""

import os
import sys
from typing import List

import pandas as pd

# Add current directory to Python path for relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ai_agents.ai_sdr.sdr.models import Company, WorkflowState
from ai_agents.ai_sdr.sdr.logging_config import clean_log, detailed_log
from ai_agents.ai_sdr.sdr.nodes.streamlined_web_enricher import StreamlinedWebEnricher
from ai_agents.ai_sdr.sdr.nodes.file_storage import serialize_company_data
from ai_agents.ai_sdr.sdr.nodes.company_list_retriever import _normalize_company_data


def validate_company_model():
    """Validate the Company model and its attributes"""
    clean_log("Testing Company model creation...")
    
    # Test minimal company creation
    minimal_company = Company(name="Test Company")
    clean_log(f"Created minimal company: {minimal_company}")
    
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
    clean_log(f"Created full company: {full_company}")
    
    # Test attribute access
    clean_log("Testing attribute access...")
    attributes = [
        'name', 'website', 'domain', 'industry', 
        'size', 'location', 'description', 'linkedin_url'
    ]
    
    for attr in attributes:
        try:
            value = getattr(minimal_company, attr)
            detailed_log(f"Minimal company.{attr} = {value}")
        except AttributeError as e:
            clean_log(f"❌ Failed to access minimal_company.{attr}: {e}", level="error")
    
    # Test serialization
    clean_log("Testing company serialization...")
    try:
        serialized = serialize_company_data(minimal_company, {"test": "data"})
        detailed_log(f"Serialized minimal company: {serialized}")
    except Exception as e:
        clean_log(f"❌ Failed to serialize minimal company: {e}", level="error")
    
    try:
        serialized = serialize_company_data(full_company, {"test": "data"})
        detailed_log(f"Serialized full company: {serialized}")
    except Exception as e:
        clean_log(f"❌ Failed to serialize full company: {e}", level="error")
    
    return minimal_company, full_company


def validate_company_list_retrieval():
    """Validate company list retrieval from different data sources"""
    clean_log("Testing company list retrieval...")
    
    # Test with a minimal DataFrame
    data = {"company": ["Company A", "Company B", "Company C"]}
    df = pd.DataFrame(data)
    
    try:
        companies = _normalize_company_data(df)
        clean_log(f"Created {len(companies)} companies from minimal DataFrame")
        for company in companies:
            detailed_log(f"Company: {company}")
    except Exception as e:
        clean_log(f"❌ Failed to normalize minimal DataFrame: {e}", level="error")
    
    # Test with a more complex DataFrame
    data = {
        "company_name": ["Company D", "Company E", "Company F"],
        "website": ["http://d.com", "http://e.com", "http://f.com"],
        "industry": ["Tech", "Finance", "Healthcare"]
    }
    df = pd.DataFrame(data)
    
    try:
        companies = _normalize_company_data(df)
        clean_log(f"Created {len(companies)} companies from complex DataFrame")
        for company in companies:
            detailed_log(f"Company: {company.name}, Website: {company.website}, Industry: {company.industry}")
    except Exception as e:
        clean_log(f"❌ Failed to normalize complex DataFrame: {e}", level="error")
    
    return companies


def validate_web_enricher(companies: List[Company]):
    """Validate web enricher with different company objects"""
    clean_log("Testing web enricher with different company objects...")
    
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
            
            detailed_log(f"Generated system prompt for {company.name}: {system_prompt}")
        except Exception as e:
            clean_log(f"❌ Failed to create web enricher for {company.name}: {e}", level="error")


def validate_workflow_state():
    """Validate WorkflowState with different company objects"""
    clean_log("Testing WorkflowState...")
    
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
    
    clean_log(f"Created WorkflowState with {len(state.companies)} companies")
    detailed_log(f"Current company: {state.current_company.name}")
    
    # Test state transitions
    state.current_company_index += 1
    state.current_company = state.companies[state.current_company_index]
    
    detailed_log(f"Transitioned to next company: {state.current_company.name}")
    
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
    
    detailed_log(f"Added enriched data for {minimal_company.name}")
    detailed_log(f"Enriched data: {state.enriched_data.get(minimal_company.name)}")
    
    return state


def main():
    """Main validation function"""
    # Use the SDR logging system instead of direct logger setup
    clean_log("=" * 60)
    clean_log("Starting model validation...")
    clean_log("=" * 60)
    
    # Validate Company model
    minimal_company, full_company = validate_company_model()
    
    # Validate company list retrieval
    companies = validate_company_list_retrieval()
    
    # Validate web enricher
    validate_web_enricher([minimal_company, full_company] + companies)
    
    # Validate workflow state
    state = validate_workflow_state()
    
    clean_log("=" * 60)
    clean_log("Model validation completed!")
    clean_log("=" * 60)


if __name__ == "__main__":
    main() 