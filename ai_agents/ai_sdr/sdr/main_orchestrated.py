#!/usr/bin/env python3
"""
Main SDR Orchestrated Workflow Runner

Executes the orchestrated workflow architecture for TMS prospect analysis.
"""

import asyncio
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any

from ai_agents.ai_sdr.sdr.main import load_configuration, create_run_directories, get_project_root, get_prompts_configuration

from agents import set_default_openai_client
from openai import AsyncOpenAI

from ai_agents.ai_sdr.sdr.models import WorkflowState
from ai_agents.ai_sdr.sdr.workflow_adapter import WorkflowAdapter
from ai_agents.ai_sdr.sdr.logging_config import setup_sdr_logging, log_workflow_start, clean_log, detailed_log

async def main(cli_config=None):
    """Main entry point for the orchestrated SDR workflow"""

    # Set up run directories
    run_directories = create_run_directories()

    # Set up logging
    setup_sdr_logging(run_directories)


    try:
        # For main_orchestrated.py, always use defaults (no interactive prompts)
        # Interactive configuration should be done via cli_app_orchestrated.py
        custom_prompts = {}
            
        # Load configuration
        config = load_configuration(run_directories, cli_config)
        
        # Add custom prompts to config if obtained
        if custom_prompts:
            config["custom_prompts"] = custom_prompts
        
        # Initialize OpenAI client
        api_key = config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            detailed_log("❌ No OpenAI API key found. Please set OPENAI_API_KEY environment variable.")
            sys.exit(1)

        detailed_log("🔧 Setting up environment...")
        client = AsyncOpenAI(api_key=api_key)
        set_default_openai_client(client)

        # Create and run orchestrated workflow
        detailed_log("\n🚀 Starting orchestrated SDR workflow...")
        detailed_log("=" * 80)

        log_workflow_start("SDR Orchestrated", config=config)
        # Use the workflow adapter with orchestrated mode
        workflow_runner = WorkflowAdapter.create_orchestrated_workflow(config)

        initial_state = WorkflowState(
            run_id=config["run_directories"]["run_id"],
            started_at=datetime.now(),
            run_directories=config["run_directories"]
        )

        # Run the workflow
        clean_log("")  # Add blank line before workflow output
        result = await workflow_runner.run(initial_state)
        clean_log("")  # Add blank line after workflow output

        # Display summary
        detailed_log("=" * 80)
        detailed_log("✅ ORCHESTRATED WORKFLOW COMPLETED SUCCESSFULLY!")
        detailed_log(f"📊 Summary:")
        detailed_log(f"   • Total companies processed: {len(result.companies)}")
        detailed_log(f"   • Total contacts found: {sum(len(contacts) for contacts in result.contacts.values())}")
        detailed_log(f"   • Files saved: {len(result.saved_files)}")

        if result.errors:
            detailed_log(f"   • ⚠️  Errors encountered: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                detailed_log(f"      - {error}")
            if len(result.errors) > 5:
                detailed_log(f"      ... and {len(result.errors) - 5} more")

        detailed_log(f"\n📁 Output files saved to:")
        detailed_log(f"   • Progress: {run_directories['progress_dir']}")
        detailed_log(f"   • Final: {run_directories['final_dir']}")

        if result.saved_files:
            detailed_log(f"\n📄 Generated files:")
            for file_path in result.saved_files[-5:]:  # Show last 5 files
                detailed_log(f"   • {os.path.basename(file_path)}")
            if len(result.saved_files) > 5:
                detailed_log(f"   ... and {len(result.saved_files) - 5} more")

    except KeyboardInterrupt:
        detailed_log("\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        detailed_log(f"\n❌ WORKFLOW FAILED: {str(e)}")
        detailed_log("Traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
