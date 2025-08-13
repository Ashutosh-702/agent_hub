#!/usr/bin/env python3
"""
Main SDR Workflow Runner

Executes the complete LangGraph workflow for TMS prospect analysis.
"""

import asyncio
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents import set_default_openai_client
from dotenv import load_dotenv
from openai import AsyncOpenAI

from ai_agents.ai_sdr.sdr.models import WorkflowState
from ai_agents.ai_sdr.sdr.graph import compile_workflow
from ai_agents.ai_sdr.sdr.prompts import get_user_prompts, load_prompts_from_file, save_prompts_to_file
from ai_agents.ai_sdr.sdr.logging_config import setup_sdr_logging, log_workflow_start, clean_log, detailed_log, get_log_mode




def get_project_root() -> str:
    """Get the absolute path to the project root directory"""
    current_file = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(current_file))  # Go up two levels from sdr/main.py


def get_output_root() -> str:
    """Get the absolute path to the output root directory"""
    return os.path.join(get_project_root(), "output")


def create_run_directories() -> Dict[str, str]:
    """Create numbered run directories for progress and final files"""
    output_root = get_output_root()
    counter_file = os.path.join(output_root, "run_counter.txt")

    # Create output directory if it doesn't exist
    os.makedirs(output_root, exist_ok=True)

    # Read or initialize counter
    try:
        with open(counter_file, 'r') as f:
            run_number = int(f.read().strip()) + 1
    except (FileNotFoundError, ValueError):
        run_number = 1

    # Save updated counter
    with open(counter_file, 'w') as f:
        f.write(str(run_number))

    run_id = f"run_{run_number:04d}"  # Format as 4-digit number with leading zeros

    directories = {
        "run_id": run_id,
        "base_dir": os.path.join(output_root, run_id),
        "progress_dir": os.path.join(output_root, run_id, "progress"),
        "final_dir": os.path.join(output_root, run_id, "final"),
        "results_dir": os.path.join(output_root, run_id, "results"),
        "logs_dir": os.path.join(output_root, run_id, "logs")
    }

    for dir_path in directories.values():
        if dir_path != run_id:  # Skip the run_id key
            os.makedirs(dir_path, exist_ok=True)

    clean_log(f"Setup complete - Run ID: {run_id}")
    detailed_log(f"📍 Output root: {output_root}")
    detailed_log(f"   Progress files: {directories['progress_dir']}")
    detailed_log(f"   Final files: {directories['final_dir']}")
    detailed_log(f"   Results files: {directories['results_dir']}")
    detailed_log(f"   Logs: {directories['logs_dir']}")

    return directories


# Removed redundant setup_logging function - use setup_sdr_logging directly


def get_prompts_configuration() -> Dict[str, str]:
    """
    Get prompts configuration from user input or file
    
    Returns:
        Dictionary of custom prompts
    """
    # First, check if custom prompts file exists (created by GUI)
    custom_prompts_file = "sdr/config/custom_prompts.json"
    
    if os.path.exists(custom_prompts_file):
        clean_log("Found custom prompts from GUI")
        custom_prompts = load_prompts_from_file(custom_prompts_file)
        if custom_prompts:
            clean_log(f"Loaded {len(custom_prompts)} custom prompts")
            return custom_prompts
    
    # If no GUI custom prompts, check for interactive vs CLI mode
    # For non-interactive execution (like GUI subprocess), skip prompts and use defaults
    if not sys.stdin.isatty():
        clean_log("Using default prompts (non-interactive mode)")
        return {}
    
    # Check if we're being called from CLI app (which already handled prompt config)
    # CLI app creates this file even if empty to signal prompts were configured
    if os.path.exists(custom_prompts_file):
        clean_log("Using default prompts")
        return {}
    
    # Interactive prompt configuration - only show in detailed mode
    detailed_log("\n" + "=" * 60)
    detailed_log("🎯 PROMPT CONFIGURATION")
    detailed_log("=" * 60)
    detailed_log("Choose how to configure prompts for the SDR workflow:")
    detailed_log("1. Interactive prompt customization")
    detailed_log("2. Load prompts from file (prompts.json)")
    detailed_log("3. Use default prompts")
    
    # Also show a clean version for terminal
    clean_log("Prompt configuration options available (interactive mode)")

    choice = input("\nEnter your choice (1-3) or press Enter for default: ").strip()
    if not choice:
        choice = "3"
        
    custom_prompts = {}

    if choice == "1":
        # Interactive prompt customization
        custom_prompts = get_user_prompts()

        # Offer to save custom prompts
        if custom_prompts:
            save_choice = input("\n💾 Save these custom prompts to file for future use? (y/n): ").strip().lower()
            if save_choice == 'y':
                prompts_file = "sdr/config/custom_prompts.json"
                save_prompts_to_file(custom_prompts, prompts_file)

    elif choice == "2":
        # Load from file
        prompts_file = input("Enter prompts file path (default: sdr/config/custom_prompts.json): ").strip()
        if not prompts_file:
            prompts_file = "sdr/config/custom_prompts.json"
        custom_prompts = load_prompts_from_file(prompts_file)

    else:
        # Use defaults
        clean_log("Using default prompts")

    return custom_prompts


def load_configuration(run_directories: Dict[str, str], cli_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Load and validate configuration with run directories and optional CLI config"""

    # Load environment variables
    load_dotenv()

    # Helper function to get value from CLI config, then env vars, then default
    def get_config_value(cli_key: str, env_key: str, default: Any = None):
        if cli_config and cli_key in cli_config:
            return cli_config[cli_key]
        return os.getenv(env_key, default)

    # Required configuration
    openai_api_key = get_config_value("OPENAI_API_KEY", "OPENAI_API_KEY")
    if not openai_api_key:
        clean_log("❌ OPENAI_API_KEY not found in configuration or environment variables", level="error")
        clean_log("Please set your OpenAI API key:")
        clean_log("export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)

    # Data source configuration
    data_source_type = get_config_value("DATA_SOURCE_TYPE", "DATA_SOURCE_TYPE", "csv")

    # Get prompts configuration - use empty dict as default since user removed prompt input
    custom_prompts = {}
    # Load custom prompts from file if CLI configured them
    if cli_config and "custom_prompts" in cli_config:
        custom_prompts = cli_config["custom_prompts"]
        clean_log(f"Using {len(custom_prompts)} custom prompts from CLI configuration")
    elif cli_config:
        custom_prompts_file = "sdr/config/custom_prompts.json"
        if os.path.exists(custom_prompts_file):
            try:
                loaded_prompts = load_prompts_from_file(custom_prompts_file)
                if loaded_prompts:
                    custom_prompts = loaded_prompts
                    clean_log(f"Loaded {len(custom_prompts)} custom prompts from CLI configuration")
            except Exception as e:
                clean_log(f"Warning: Could not load custom prompts: {e}", "warning")

    config = {
        "openai_api_key": openai_api_key,
        "data_source": {
            "type": data_source_type,
            "file_path": get_config_value("CSV_FILE_PATH", "CSV_FILE_PATH", "ai_agents/data/company_names.csv"),
            "sheet_url": get_config_value("GOOGLE_SHEET_URL", "GOOGLE_SHEET_URL"),
            "worksheet_name": get_config_value("GOOGLE_WORKSHEET_NAME", "GOOGLE_WORKSHEET_NAME"),
            "campaign_id": get_config_value("CAMPAIGN_ID","CAMPAIGN_ID")
        },
        "clearbit_api_key": get_config_value("CLEARBIT_API_KEY", "CLEARBIT_API_KEY"),
        "browser_timeout": int(get_config_value("BROWSER_TIMEOUT", "BROWSER_TIMEOUT", "30")),
        "max_companies": int(get_config_value("MAX_COMPANIES", "MAX_COMPANIES", "100")),
        "output_directory": get_config_value("OUTPUT_DIRECTORY", "OUTPUT_DIRECTORY", get_output_root()),
        "hubspot_api_key": get_config_value("HUBSPOT_API_KEY", "HUBSPOT_API_KEY"),
        "hubspot_owner_email": get_config_value("HUBSPOT_OWNER_EMAIL", "HUBSPOT_OWNER_EMAIL", "atharvashetye@gofynd.com"),
        "create_hubspot_contacts": str(get_config_value("CREATE_HUBSPOT_CONTACTS", "CREATE_HUBSPOT_CONTACTS", "true")).lower() == "true",
        "custom_prompts": custom_prompts,
        "run_directories": run_directories,
    }

    # Clean config summary
    api_status = "✓" if openai_api_key else "✗"
    hubspot_status = "✓" if config['hubspot_api_key'] else "✗"
    config_source = "CLI" if cli_config else "env"
    clean_log(f"Config loaded from {config_source} (OpenAI: {api_status}, HubSpot: {hubspot_status})")
    
    # Detailed config info for detailed mode
    detailed_log(f"⚙️  Configuration loaded for run: {run_directories['run_id']}")
    detailed_log(f"  - Config source: {'CLI application' if cli_config else 'Environment variables'}")
    detailed_log(f"  - Data source: {data_source_type}")
    detailed_log(f"  - OpenAI API: {'✅ Configured' if openai_api_key else '❌ Missing'}")
    detailed_log(f"  - HubSpot API: {'✅ Configured' if config['hubspot_api_key'] else '⚠️  Optional'}")
    detailed_log(f"  - HubSpot contacts: {'✅ Enabled' if config['create_hubspot_contacts'] else '❌ Disabled'}")
    detailed_log(f"  - HubSpot owner: {config['hubspot_owner_email']}")
    detailed_log(f"  - Custom prompts: {'✅ Using custom' if custom_prompts else '📝 Using defaults'}")

    return config


def run_model_validation():
    """Run model validation to check for issues"""
    clean_log("🧪 Running model validation...")

    try:
        from validate_models import main as run_validation
        run_validation()
        clean_log("✅ Model validation completed successfully")
        return True
    except Exception as e:
        clean_log(f"❌ Model validation failed: {e}", level="error")
        detailed_log(traceback.format_exc())
        return False


async def run_tms_workflow(config: Dict[str, Any]) -> WorkflowState:
    """
    Run the complete TMS workflow with enhanced error handling and logging

    Args:
        config: Configuration dictionary containing API keys, file paths, etc.

    Returns:
        Final workflow state with all results
    """

    clean_log("🚀 Starting TMS Workflow Execution...")

    try:
        # Initialize state
        initial_state = WorkflowState(
            run_id=config["run_directories"]["run_id"],
            started_at=datetime.now(),
            run_directories=config["run_directories"]
        )

        # Create and run the workflow
        workflow = compile_workflow()

        clean_log("📝 Executing workflow graph...")

        final_state = await workflow.ainvoke(
            initial_state,
            config={"configurable": config, "recursion_limit": 10000},
        )

        # Set completion time
        final_state["completed_at"] = datetime.now()

        clean_log("✅ TMS Workflow completed successfully")
        return final_state

    except Exception as e:
        clean_log(f"❌ TMS Workflow failed: {e}", level="error")
        detailed_log(traceback.format_exc())

        # Create error state
        error_state = WorkflowState(
            companies=[],
            enriched_data={},
            errors=[f"Workflow failed: {str(e)}"],
            run_id=config["run_directories"]["run_id"],
            run_directories=config.get("run_directories", {}),
            started_at=datetime.now(),
            completed_at=datetime.now(),
            all_linkedin_profiles=[]
        )
        error_state.errors.append(f"Workflow failed: {str(e)}")

        return error_state


def print_workflow_summary(final_state: WorkflowState):
    """Print workflow summary with clean or detailed output based on LOG_MODE"""

    run_id = final_state["run_id"]
    total_companies = len(final_state["companies"])
    linkedin_profiles = len(final_state.get('all_linkedin_profiles', []))
    
    # Calculate HubSpot stats
    hubspot_contacts_created = 0
    hubspot_duplicates = 0
    hubspot_failed = 0
    
    for company_data in final_state["enriched_data"].values():
        hubspot_results = company_data.get('hubspot_results', {})
        if hubspot_results:
            hubspot_contacts_created += hubspot_results.get('created_count', 0)
            hubspot_duplicates += hubspot_results.get('duplicate_count', 0)
            hubspot_failed += hubspot_results.get('failed_count', 0)

    error_count = len(final_state["errors"])
    
    # Calculate categorized error counts
    error_summary = final_state.get("error_summary", {})
    skipped_count = len(error_summary.skipped_companies)
    prospect_failures = len(error_summary.prospect_enrichment_failures)
    hubspot_failures = len(error_summary.hubspot_failures)
    web_failures = len(error_summary.web_enrichment_failures)
    total_categorized_errors = skipped_count + prospect_failures + hubspot_failures + web_failures
    
    # Clean summary for terminal
    if get_log_mode() == "clean":
        status = "✓" if total_categorized_errors == 0 else f"⚠ ({total_categorized_errors} issues)"
        clean_log(f"Workflow completed {status}")
        clean_log(f"Results: {total_companies} companies, {linkedin_profiles} LinkedIn profiles, {hubspot_contacts_created} HubSpot contacts")
        
        if total_categorized_errors > 0:
            # Show brief error breakdown
            error_parts = []
            if skipped_count > 0:
                error_parts.append(f"{skipped_count} skipped")
            if prospect_failures > 0:
                error_parts.append(f"{prospect_failures} LinkedIn failures")  
            if hubspot_failures > 0:
                error_parts.append(f"{hubspot_failures} HubSpot failures")
            if web_failures > 0:
                error_parts.append(f"{web_failures} web failures")
            
            if error_parts:
                clean_log(f"Issues breakdown: {', '.join(error_parts)}", "warning")
            clean_log(f"See detailed logs: {final_state.get('run_directories', {}).get('logs_dir', 'output')}/workflow.log", "warning")
    
    # Detailed summary for verbose mode or file logging
    if get_log_mode() == "detailed":
        detailed_log("")
        detailed_log("═" * 80)
        detailed_log(f"🚀 SDR WORKFLOW EXECUTION COMPLETED")
        detailed_log(f"📊 Run ID: {run_id}")
        detailed_log("═" * 80)

        detailed_log("")
        detailed_log("✅ Processing completed without errors" if not final_state["errors"] else "⚠️ Processing completed with some errors")
        detailed_log("🏢 All companies have been analyzed and enriched")
        detailed_log("📊 Results are ready for review")

        # Core statistics in clean format
        detailed_log("")
        detailed_log("📊 FINAL WORKFLOW STATISTICS:")
        detailed_log("─" * 50)
        detailed_log(f"🔗 LinkedIn URLs Found: {linkedin_profiles}")
        detailed_log(f"📧 HubSpot Contacts Created: {hubspot_contacts_created}")
        detailed_log(f"🔄 Duplicates Found: {hubspot_duplicates}")
        detailed_log(f"❌ Failed Contacts: {hubspot_failed}")

        # Detailed error summary by category
        if total_categorized_errors > 0:
             detailed_log("")
             detailed_log("⚠️ ISSUES ENCOUNTERED BY CATEGORY:")
             detailed_log("─" * 50)
             
             # Skipped companies
             if skipped_count > 0:
                 detailed_log(f"🔸 SKIPPED COMPANIES ({skipped_count}):")
                 for i, skipped in enumerate(error_summary.get("skipped_companies", [])[:3], 1):
                     company = skipped.get("company", "Unknown")
                     reason = skipped.get("reason", "Unknown reason")
                     detailed_log(f"   {i}. {company} - {reason}", "warning")
                 if skipped_count > 3:
                     detailed_log(f"   ... and {skipped_count - 3} more skipped companies", "warning")
                 detailed_log("")
             
             # LinkedIn enrichment failures
             if prospect_failures > 0:
                 detailed_log(f"🔸 LINKEDIN ENRICHMENT FAILURES ({prospect_failures}):")
                 for i, failure in enumerate(error_summary.get("prospect_enrichment_failures", [])[:3], 1):
                     company = failure.get("company", "Unknown")
                     error = failure.get("error", "Unknown error")
                     detailed_log(f"   {i}. {company} - {error}", "warning")
                 if prospect_failures > 3:
                     detailed_log(f"   ... and {prospect_failures - 3} more LinkedIn failures", "warning")
                 detailed_log("")
             
             # HubSpot failures
             if hubspot_failures > 0:
                 detailed_log(f"🔸 HUBSPOT CREATION FAILURES ({hubspot_failures}):")
                 for i, failure in enumerate(error_summary.get("hubspot_failures", [])[:3], 1):
                     contact = failure.get("contact", "Unknown")
                     error = failure.get("error", "Unknown error")
                     detailed_log(f"   {i}. {contact} - {error}", "warning")
                 if hubspot_failures > 3:
                     detailed_log(f"   ... and {hubspot_failures - 3} more HubSpot failures", "warning")
                 detailed_log("")
             
             # Web enrichment failures
             if web_failures > 0:
                 detailed_log(f"🔸 WEB ENRICHMENT FAILURES ({web_failures}):")
                 for i, failure in enumerate(error_summary.get("web_enrichment_failures", [])[:3], 1):
                     company = failure.get("company", "Unknown")
                     error = failure.get("error", "Unknown error")
                     detailed_log(f"   {i}. {company} - {error}", "warning")
                 if web_failures > 3:
                     detailed_log(f"   ... and {web_failures - 3} more web failures", "warning")
                 detailed_log("")
             
             # General errors (legacy)
             if error_count > 0:
                 detailed_log(f"🔸 OTHER ISSUES ({error_count}):")
                 for i, error in enumerate(final_state["errors"][:2], 1):
                     detailed_log(f"   {i}. {error}", "warning")
                 if error_count > 2:
                     detailed_log(f"   ... and {error_count - 2} more general issues", "warning")

        # File locations
        run_dirs = final_state.get("run_directories", {})
        detailed_log("")
        detailed_log("📁 Results Location:")
        detailed_log("─" * 30)
        detailed_log(f"🏠 Main Results: {run_dirs.get('final_dir', 'output')}/final/")
        detailed_log(f"📄 Detailed Logs: {run_dirs.get('logs_dir', 'output')}/logs/")
        detailed_log(f"🎯 HubSpot Data: Check your HubSpot contacts")

        # Clear completion message
        detailed_log("")
        detailed_log("🎉 WORKFLOW COMPLETED SUCCESSFULLY! 🎉")
        detailed_log("─" * 50)
        detailed_log("📌 Processing completed without errors" if not final_state["errors"] else f"📌 Processing completed with {error_count} minor issues")
        detailed_log("🏢 All companies have been analyzed and enriched")  
        detailed_log("📊 Results are ready for review")
        detailed_log("")
        detailed_log("═" * 80)


async def graceful_shutdown():
    """Handle graceful shutdown of async resources"""
    detailed_log("🔄 Performing graceful shutdown...")
    
    try:
        # Get current task to exclude it from cancellation
        current_task = asyncio.current_task()
        
        # Cancel any remaining tasks except the current one
        pending = [task for task in asyncio.all_tasks() if not task.done() and task != current_task]
        
        if pending:
            detailed_log(f"🔄 Cancelling {len(pending)} pending tasks...")
            
            # Cancel all tasks
            for task in pending:
                if not task.cancelled():
                    task.cancel()
            
            # Wait for tasks to complete cancellation with individual handling
            if pending:
                try:
                    # Use asyncio.wait instead of asyncio.gather to handle cancellations better
                    done, still_pending = await asyncio.wait(
                        pending, 
                        timeout=3.0, 
                        return_when=asyncio.ALL_COMPLETED
                    )
                    
                    if still_pending:
                        detailed_log(f"⚠️ {len(still_pending)} tasks didn't complete cancellation within timeout", "warning")
                        # Force cancel any remaining tasks
                        for task in still_pending:
                            if not task.cancelled():
                                task.cancel()
                    
                except Exception as e:
                    detailed_log(f"Task cancellation completed with exceptions: {e}", "debug")
        else:
            detailed_log("✅ No pending tasks to cancel")
            
    except Exception as e:
        detailed_log(f"⚠️ Error during graceful shutdown: {e}", "warning")
    
    detailed_log("✅ Graceful shutdown completed")


async def main(cli_config=None):
    # Set up run directories
    run_directories = create_run_directories()

    # Set up logging
    setup_sdr_logging(run_directories)

    try:
        # Get prompts configuration first (if not from CLI)
        if not cli_config:
            custom_prompts = get_prompts_configuration()
        else:
            custom_prompts = {}
            
        # Load configuration
        config = load_configuration(run_directories, cli_config)
        
        # Add custom prompts to config if obtained
        if custom_prompts:
            config["custom_prompts"] = custom_prompts

        # Initialize OpenAI client
        openai_client = AsyncOpenAI(api_key=config.get('openai_api_key'))
        set_default_openai_client(openai_client)

        # Start SDR workflow
        clean_log("Starting SDR workflow execution...")
        detailed_log("\n" + "=" * 60)
        detailed_log("🔍 SDR WORKFLOW EXECUTOR")
        detailed_log("=" * 60)
        
        log_workflow_start("SDR Workflow", config)

        # Run the workflow
        final_state = await run_tms_workflow(config)

        # Print summary
        print_workflow_summary(final_state)
    #
    except KeyboardInterrupt:
        clean_log("⚠️ Workflow interrupted by user", "warning")
        detailed_log("\n" + "=" * 60)
        detailed_log("⚠️ WORKFLOW INTERRUPTED")
        detailed_log("=" * 60)
        detailed_log("Workflow execution was interrupted. Partial results may be available in the output directory.")

    except Exception as e:
        clean_log(f"❌ Workflow failed with error: {e}", "error")
        detailed_log(traceback.format_exc())
        clean_log(f"See logs: {run_directories['logs_dir']}/workflow.log", "error")
        detailed_log("\n" + "=" * 60)
        detailed_log("❌ WORKFLOW FAILED")
        detailed_log("=" * 60)
        detailed_log(f"Error: {e}")
        detailed_log(f"See logs for details: {run_directories['logs_dir']}/workflow.log")

    finally:
        # Always perform graceful shutdown with error handling
        try:
            await graceful_shutdown()
        except Exception as shutdown_error:
            clean_log(f"⚠️ Error during final shutdown: {shutdown_error}", "warning")

    clean_log("SDR workflow execution completed")
    detailed_log("\n" + "=" * 60)
    detailed_log("SDR Workflow Execution Completed")
    detailed_log("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        clean_log("Workflow interrupted by user", "warning")
    except Exception as e:
        clean_log(f"Fatal error: {e}", "error")
        detailed_log(traceback.format_exc())
