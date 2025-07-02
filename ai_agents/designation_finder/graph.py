"""
LangGraph workflow for Designation Finder
Simple linear workflow: LinkedIn search → CSV logging → END
Single company processing per workflow run
"""
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from ai_agents.designation_finder.models import DesignationFinderState
from ai_agents.designation_finder.nodes.linkedin_designation_finder import linkedin_designation_finder
from ai_agents.designation_finder.nodes.csv_logger import csv_logger


def create_workflow_graph() -> StateGraph:
    """Create the linear LangGraph workflow for single company processing"""
    
    print("🏗️ Building Designation Finder workflow graph (single company)")

    # Create the state graph
    workflow = StateGraph(DesignationFinderState)

    # Add nodes - simplified for single company processing
    nodes_config = {
        "linkedin_designation_finder": linkedin_designation_finder,
        "csv_logger": csv_logger
    }
    
    print(f"➕ Adding {len(nodes_config)} workflow nodes")
    
    for node_name, node_func in nodes_config.items():
        workflow.add_node(node_name, node_func)

    # Set entry point - start with LinkedIn search
    workflow.set_entry_point("linkedin_designation_finder")
    
    print("🔗 Configuring workflow edges")

    # Linear flow: LinkedIn search → CSV logging → END
    workflow.add_edge("linkedin_designation_finder", "csv_logger")
    workflow.add_edge("csv_logger", END)
    
    print("✅ Workflow graph created successfully")
    print("   Flow: LinkedIn Search → CSV Log → END")

    return workflow


def compile_workflow() -> CompiledStateGraph:
    """Compile and return the workflow"""
    print("⚙️ Compiling Designation Finder workflow")
    
    workflow = create_workflow_graph()
    compiled_workflow = workflow.compile()
    
    print("✅ Workflow compiled successfully")
    
    return compiled_workflow