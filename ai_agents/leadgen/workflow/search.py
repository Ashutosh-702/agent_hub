"""
Lead generation workflows combining core_sdr and ai_sdr functionality.
"""

import os
from typing import Dict, Any

from ai_agents.core_sdr.src.cli.main import process_company_search


async def run_basic_workflow(query: str) -> Dict[str, Any]:
    """
    Run Company workflow - just company search using core_sdr.
    """


    print(f"Running Company workflow for query: {query}")
    return await process_company_search(query)

from ai_agents.ai_sdr.cli_app_orchestrated import OrchestratedCLIApp
async def run_full_workflow(query: str) -> Dict[str, Any]:
    """
    Run Company + Employee workflow.
    """

    print(f"Running Company + Employee workflow for query: {query}")
    basic_results = await process_company_search(query)
    app = OrchestratedCLIApp()
    app.config = {
        "DATA_SOURCE_TYPE": "csv",
        "CSV_FILE_PATH": basic_results["csv_path"],
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
    }

    await app.run()
    
    return {
        "basic_results": basic_results,
    }