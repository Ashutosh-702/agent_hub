#!/usr/bin/env python3
"""
Test script to validate Pydantic models for SDR workflow

This script tests the models to ensure they work correctly with LangGraph.
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

try:
    from sdr.models import WorkflowState, ErrorSummary, Company, Contact, NodeResult
    from datetime import datetime
    
    def test_error_summary():
        """Test ErrorSummary model"""
        print("Testing ErrorSummary...")
        
        # Test empty initialization
        error_summary = ErrorSummary()
        assert len(error_summary.skipped_companies) == 0
        assert len(error_summary.prospect_enrichment_failures) == 0
        assert len(error_summary.hubspot_failures) == 0
        assert len(error_summary.web_enrichment_failures) == 0
        assert len(error_summary.general_errors) == 0
        print("✅ ErrorSummary empty initialization works")
        
        # Test with data
        error_summary = ErrorSummary(
            skipped_companies=[{"company": "Test Corp", "reason": "Not relevant"}],
            general_errors=["Test error"]
        )
        assert len(error_summary.skipped_companies) == 1
        assert len(error_summary.general_errors) == 1
        print("✅ ErrorSummary with data works")
        
    def test_workflow_state():
        """Test WorkflowState model"""
        print("Testing WorkflowState...")
        
        # Test basic initialization (this was failing before)
        state = WorkflowState()
        assert isinstance(state.error_summary, ErrorSummary)
        assert len(state.companies) == 0
        assert len(state.errors) == 0
        print("✅ WorkflowState default initialization works")
        
        # Test initialization with explicit ErrorSummary
        error_summary = ErrorSummary()
        state = WorkflowState(
            companies=[],
            enriched_data={},
            errors=[],
            error_summary=error_summary,
            run_id="test_001",
            started_at=datetime.now(),
            all_linkedin_profiles=[],
            run_directories={"run_dir": "/tmp/test"}
        )
        assert isinstance(state.error_summary, ErrorSummary)
        assert state.run_id == "test_001"
        print("✅ WorkflowState explicit initialization works")
        
        # Test model validation
        try:
            # This should work now with our validator
            state_dict = {
                "companies": [],
                "enriched_data": {},
                "errors": [],
                "run_id": "test_002",
                "started_at": datetime.now(),
                "all_linkedin_profiles": [],
                "run_directories": {"run_dir": "/tmp/test"}
                # Note: no error_summary - should be auto-created by validator
            }
            state = WorkflowState(**state_dict)
            assert isinstance(state.error_summary, ErrorSummary)
            print("✅ WorkflowState auto-initialization of error_summary works")
            
        except Exception as e:
            print(f"❌ WorkflowState validation failed: {e}")
            raise
    
    def test_other_models():
        """Test other models"""
        print("Testing other models...")
        
        # Test Company
        company = Company(name="Test Company", website="https://test.com")
        assert company.name == "Test Company"
        assert company.website == "https://test.com"
        print("✅ Company model works")
        
        # Test Contact
        contact = Contact(name="John Doe", company_name="Test Company", email="john@test.com")
        assert contact.name == "John Doe"
        assert contact.company_name == "Test Company"
        print("✅ Contact model works")
        
        # Test NodeResult
        result = NodeResult(success=True, message="Test successful")
        assert result.success is True
        assert result.message == "Test successful"
        assert len(result.data) == 0
        print("✅ NodeResult model works")
    
    def run_all_tests():
        """Run all model tests"""
        print("🧪 Running Pydantic Model Tests\n")
        
        try:
            test_error_summary()
            print()
            test_workflow_state()
            print()
            test_other_models()
            print()
            print("🎉 All model tests passed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        success = run_all_tests()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the correct directory and dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 