#!/usr/bin/env python3
"""
Test workflow initialization to ensure GUI workflow starts correctly

This script tests the workflow initialization process that was failing in the GUI.
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent  # agent_hub root
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(script_dir))

try:
    from sdr.models import WorkflowState, ErrorSummary
    from sdr.main import create_run_directories
    from sdr.graph import compile_workflow
    from datetime import datetime
    
    def test_gui_workflow_initialization():
        """Test the exact workflow initialization that GUI uses"""
        print("Testing GUI workflow initialization...")
        
        try:
            # Create run directories (same as GUI)
            run_directories = create_run_directories()
            print(f"✅ Run directories created: {run_directories['run_id']}")
            
            # Initialize state exactly like GUI does (with our fix)
            initial_state = WorkflowState(
                companies=[],
                enriched_data={},
                errors=[],
                error_summary=ErrorSummary(),  # Explicit initialization
                run_id=run_directories["run_id"],
                started_at=datetime.now(),
                all_linkedin_profiles=[],
                run_directories=run_directories
            )
            print("✅ WorkflowState initialized successfully")
            
            # Compile workflow (this is where the validation error occurred)
            workflow = compile_workflow()
            print("✅ Workflow compiled successfully")
            
            # Test that the state can be converted to dict for LangGraph
            state_dict = initial_state.model_dump()
            assert 'error_summary' in state_dict
            assert isinstance(state_dict['error_summary'], dict)
            print("✅ State serialization works")
            
            # Test that we can reconstruct the state from dict
            reconstructed_state = WorkflowState(**state_dict)
            assert isinstance(reconstructed_state.error_summary, ErrorSummary)
            print("✅ State deserialization works")
            
            print("🎉 GUI workflow initialization test passed!")
            return True
            
        except Exception as e:
            print(f"❌ GUI workflow initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_workflow_state_validation():
        """Test various WorkflowState initialization scenarios"""
        print("Testing WorkflowState validation scenarios...")
        
        # Test 1: Empty initialization
        try:
            state = WorkflowState()
            assert isinstance(state.error_summary, ErrorSummary)
            print("✅ Empty initialization works")
        except Exception as e:
            print(f"❌ Empty initialization failed: {e}")
            return False
        
        # Test 2: Partial initialization (missing error_summary)
        try:
            state = WorkflowState(
                companies=[],
                run_id="test_123"
            )
            assert isinstance(state.error_summary, ErrorSummary)
            print("✅ Partial initialization (auto error_summary) works")
        except Exception as e:
            print(f"❌ Partial initialization failed: {e}")
            return False
        
        # Test 3: Dict-based initialization (LangGraph style)
        try:
            state_data = {
                "companies": [],
                "enriched_data": {},
                "errors": [],
                "run_id": "test_456",
                "run_directories": {"run_dir": "/tmp/test"}
            }
            state = WorkflowState(**state_data)
            assert isinstance(state.error_summary, ErrorSummary)
            print("✅ Dict-based initialization works")
        except Exception as e:
            print(f"❌ Dict-based initialization failed: {e}")
            return False
        
        print("🎉 WorkflowState validation tests passed!")
        return True
    
    def run_all_tests():
        """Run all initialization tests"""
        print("🔧 Testing Workflow Initialization\n")
        
        success = True
        
        success &= test_workflow_state_validation()
        print()
        success &= test_gui_workflow_initialization()
        
        if success:
            print("\n🎉 All workflow initialization tests passed!")
            print("The GUI should now work without Pydantic validation errors.")
        else:
            print("\n❌ Some tests failed - there may still be issues.")
        
        return success
    
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