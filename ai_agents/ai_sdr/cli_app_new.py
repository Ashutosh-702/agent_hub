#!/usr/bin/env python3
"""
AI SDR Agent - Interactive CLI Application for Orchestrated Workflow

User-friendly command line interface with guided configuration for the orchestrated AI SDR workflow.
This is the CLI entry point for the orchestrated (per-company) architecture.
"""

import os
import sys

import requests
from config.loaded_config import loaded_config
# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import json
import asyncio
from typing import Dict
from pathlib import Path
from datetime import datetime
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def setup_basic_logging():
    """Setup basic logging for launcher errors"""
    try:
        from ai_agents.ai_sdr.sdr.logging_config import clean_log, prompt_log
        return clean_log, prompt_log
    except ImportError:
        # Fallback to print if logging not available
        fallback = lambda msg, level="info": print(f"[{level.upper()}] {msg}")
        return fallback, print


try:
    from ai_agents.ai_sdr.sdr.main_orchestrated import main as run_orchestrated_workflow
    from ai_agents.ai_sdr.sdr.validate_models import main as validate_models
    from ai_agents.ai_sdr.sdr.logging_config import clean_log, prompt_log
except ImportError as e:
    log, prompt_log = setup_basic_logging()
    prompt_log(f"❌ Import error: {e}")
    prompt_log("Please ensure all dependencies are installed:")
    prompt_log("pip install -r requirements.txt")
    prompt_log(f"Current working directory: {os.getcwd()}")
    prompt_log(f"Python path: {sys.path[:3]}")
    sys.exit(1)


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class OrchestratedCLIApp:
    """Interactive CLI application for orchestrated AI SDR workflow configuration"""

    def __init__(self):
        self.config = {}
        self.current_dir = Path(__file__).parent
        self.env_file_path = self.current_dir / ".env"
        self.custom_prompts_file = self.current_dir / "sdr" / "config" / "custom_prompts.json"

    def print_header(self):
        """Print application header"""
        prompt_log(f"\n{Colors.CYAN}{'=' * 70}{Colors.END}")
        prompt_log(f"{Colors.BOLD}{Colors.BLUE}🤖 AI SDR Agent - Orchestrated Workflow Configuration{Colors.END}")
        prompt_log(f"{Colors.CYAN}{'=' * 70}{Colors.END}")
        prompt_log(f"{Colors.YELLOW}Welcome to the orchestrated AI SDR workflow!{Colors.END}")
        prompt_log(f"{Colors.YELLOW}This version processes companies individually for better control.{Colors.END}\n")

    def print_section(self, title: str):
        """Print section header"""
        prompt_log(f"\n{Colors.CYAN}{'─' * 50}{Colors.END}")
        prompt_log(f"{Colors.BOLD}{Colors.BLUE}📋 {title}{Colors.END}")
        prompt_log(f"{Colors.CYAN}{'─' * 50}{Colors.END}")

    def print_info(self, message: str):
        """Print info message"""
        prompt_log(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

    def print_success(self, message: str):
        """Print success message"""
        prompt_log(f"{Colors.GREEN}✅ {message}{Colors.END}")

    def print_warning(self, message: str):
        """Print warning message"""
        prompt_log(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

    def print_error(self, message: str):
        """Print error message"""
        prompt_log(f"{Colors.RED}❌ {message}{Colors.END}")

    def get_input(self, prompt: str, default: str = None, required: bool = False) -> str:
        """Get user input with optional default and validation"""
        if default:
            full_prompt = f"{Colors.YELLOW}{prompt} [{default}]: {Colors.END}"
        else:
            full_prompt = f"{Colors.YELLOW}{prompt}: {Colors.END}"

        while True:
            value = input(full_prompt).strip()
            if not value and default:
                return default
            if value or not required:
                return value
            prompt_log(f"{Colors.RED}This field is required. Please enter a value.{Colors.END}")

    def get_choice(self, prompt: str, choices: list, default: int = None) -> int:
        """Get user choice from a list of options"""
        prompt_log(f"\n{Colors.YELLOW}{prompt}{Colors.END}")
        for i, choice in enumerate(choices, 1):
            marker = f" (default)" if default == i else ""
            prompt_log(f"{Colors.BLUE}  {i}. {choice}{marker}{Colors.END}")

        while True:
            try:
                choice_str = input(f"\n{Colors.YELLOW}Enter your choice (1-{len(choices)}): {Colors.END}").strip()
                if not choice_str and default:
                    return default
                choice_num = int(choice_str)
                if 1 <= choice_num <= len(choices):
                    return choice_num
                else:
                    prompt_log(f"{Colors.RED}Please enter a number between 1 and {len(choices)}.{Colors.END}")
            except ValueError:
                prompt_log(f"{Colors.RED}Please enter a valid number.{Colors.END}")

    def check_existing_env(self) -> Dict[str, str]:
        """Check for existing .env file and load values"""
        existing_config = {}
        if self.env_file_path.exists():
            try:
                with open(self.env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_config[key.strip()] = value.strip().strip('"\'')
                self.print_success(f"Found existing .env file with {len(existing_config)} variables")
            except Exception as e:
                self.print_warning(f"Could not read existing .env file: {e}")
        return existing_config

    def configure_api_keys(self, existing_config: Dict[str, str]):
        """Configure API keys"""
        self.print_section("API Configuration")

        # OpenAI API Key (Required)
        self.print_info("OpenAI API key is required for the AI research agents")
        current_openai = existing_config.get("OPENAI_API_KEY", "")
        if current_openai:
            self.print_success(f"Current OpenAI key: {current_openai[:10]}...{current_openai[-4:]}")
            use_existing = self.get_choice("Use existing OpenAI API key?", ["Yes", "Enter new key"], 1)
            if use_existing == 1:
                self.config["OPENAI_API_KEY"] = current_openai
            else:
                self.config["OPENAI_API_KEY"] = self.get_input("Enter OpenAI API key", required=True)
        else:
            self.config["OPENAI_API_KEY"] = self.get_input("Enter OpenAI API key", required=True)

        # HubSpot API Key (Optional)
        self.print_info("HubSpot integration is optional but enables automatic contact creation")
        current_hubspot = existing_config.get("HUBSPOT_API_KEY", "")
        if current_hubspot:
            self.print_success(f"Current HubSpot key: {current_hubspot[:10]}...{current_hubspot[-4:]}")
            use_existing = self.get_choice("Use existing HubSpot API key?", ["Yes", "Enter new key", "Skip HubSpot"], 1)
            if use_existing == 1:
                self.config["HUBSPOT_API_KEY"] = current_hubspot
            elif use_existing == 2:
                new_key = self.get_input("Enter HubSpot API key (or press Enter to skip)")
                if new_key:
                    self.config["HUBSPOT_API_KEY"] = new_key
        else:
            hubspot_key = self.get_input("Enter HubSpot API key (or press Enter to skip)")
            if hubspot_key:
                self.config["HUBSPOT_API_KEY"] = hubspot_key

        # HubSpot Owner Email
        if self.config.get("HUBSPOT_API_KEY"):
            current_email = existing_config.get("HUBSPOT_OWNER_EMAIL", "")
            self.config["HUBSPOT_OWNER_EMAIL"] = self.get_input(
                "Enter HubSpot owner email (for contact assignment)",
                current_email or "user@company.com"
            )

    async def configure_data_source(self, existing_config: Dict[str, str]):
        """Configure data source settings"""
        self.print_section("Data Source Configuration")

        # Data source type
        current_type = existing_config.get("DATA_SOURCE_TYPE", "csv")
        source_choice = self.get_choice(
            "Select your data source type:",
            ["CSV file", "Excel file", "Google Sheet", "MongoDB"],
            1 if current_type == "csv" else 2 if current_type == "excel" else 3 if current_type == "google_sheets" else 4
        )

        if source_choice == 1:
            self.config["DATA_SOURCE_TYPE"] = "csv"
            current_path = existing_config.get("CSV_FILE_PATH", "ai_agents/data/company_names.csv")
            self.config["CSV_FILE_PATH"] = self.get_input(
                f"Enter path to your CSV file",
                current_path
            )
        elif source_choice == 2:
            self.config["DATA_SOURCE_TYPE"] = "excel"
            current_path = existing_config.get("CSV_FILE_PATH", "ai_agents/data/company_names.xlsx")
            self.config["CSV_FILE_PATH"] = self.get_input(
                f"Enter path to your Excel file",
                current_path
            )
        elif source_choice == 3:
            self.config["DATA_SOURCE_TYPE"] = "google_sheets"
            current_url = existing_config.get("GOOGLE_SHEET_URL", "")
            self.config["GOOGLE_SHEET_URL"] = self.get_input(
                "Enter Google Sheet URL",
                current_url,
                required=True
            )
            current_worksheet = existing_config.get("GOOGLE_WORKSHEET_NAME", "Sheet1")
            self.config["GOOGLE_WORKSHEET_NAME"] = self.get_input(
                "Enter worksheet name",
                current_worksheet
            )
        else:
            self.config["DATA_SOURCE_TYPE"] = "mongo"
            self.mongo_uri = self.get_input(
                "MONGO_LINKEDIN_SDR_READ_WRITE",
                existing_config.get("MONGO_LINKEDIN_SDR_READ_WRITE", "mongodb://localhost:27017"),
                required=True
            )
            self.db_name = self.get_input(
                "Database name",
                existing_config.get("MONGO_DB_NAME", "linkedin_sdr"),
                required=True
            )

    async def claim_and_run_mongo_campaigns(self):
        """Claim pending campaigns and process them sequentially in distributed-safe mode."""

        while True:
            BASE_URL = loaded_config.base_url
            response = requests.get(f"{BASE_URL}/api/v1/fetch_and_claim_first_campaign?", verify=False, timeout=30)
            claimed = response.json()

            if claimed.get("status") == "success" and "config" not in claimed:
                self.print_success("No pending campaigns left")
                break
            ai_sdr_custom_config = claimed.get("config",{})
            campaign_id =ai_sdr_custom_config.get("CAMPAIGN_ID","")

            if ai_sdr_custom_config:
                self.config.update(ai_sdr_custom_config)

            self.print_section(f"Processing Campaign: {campaign_id}")
            try:
                await self.run_orchestrated_workflow(with_monitoring=False)
                requests.post(f"{BASE_URL}/api/v1/update_campaign_status",params={"campaign_id": campaign_id, "status": "processed"}, verify=False, timeout=30)
            except BaseException as e:
                self.print_error(f"Error processing campaign {campaign_id}: {e}")
                requests.post(F"{BASE_URL}/api/v1/update_campaign_status",params={"campaign_id": campaign_id, "status": "failed"}, verify=False, timeout=30)

    def configure_processing_options(self, existing_config: Dict[str, str]):
        """Configure processing options with orchestrated-specific settings"""
        self.print_section("Processing Options")

        # Max companies
        current_max = existing_config.get("MAX_COMPANIES", "100")
        self.config["MAX_COMPANIES"] = self.get_input(
            "Maximum number of companies to process",
            current_max
        )

        # Browser timeout
        current_timeout = existing_config.get("BROWSER_TIMEOUT", "30")
        self.config["BROWSER_TIMEOUT"] = self.get_input(
            "Browser timeout in seconds",
            current_timeout
        )

        # Orchestrated-specific: Parallel processing
        self.print_info("The orchestrated workflow can process companies in parallel for faster execution")
        parallel_choice = self.get_choice(
            "Enable parallel company processing?",
            ["No - Process companies sequentially (safer)", "Yes - Process companies in parallel (faster)"],
            1
        )
        self.config["PARALLEL_PROCESSING"] = "true" if parallel_choice == 2 else "false"

        if parallel_choice == 2:
            current_workers = existing_config.get("MAX_WORKERS", "5")
            self.config["MAX_WORKERS"] = self.get_input(
                "Maximum number of parallel workers",
                current_workers
            )

        # HubSpot contact creation
        if self.config.get("HUBSPOT_API_KEY"):
            current_create = existing_config.get("CREATE_HUBSPOT_CONTACTS", "true")
            create_choice = self.get_choice(
                "Create HubSpot contacts automatically?",
                ["Yes", "No"],
                1 if current_create.lower() == "true" else 2
            )
            self.config["CREATE_HUBSPOT_CONTACTS"] = "true" if create_choice == 1 else "false"

    def configure_prompts(self):
        """Configure custom prompts with enhanced options"""
        self.print_section("Enhanced Prompt Customization")

        # Check for existing custom prompts
        existing_prompts = {}
        if self.custom_prompts_file.exists():
            try:
                with open(self.custom_prompts_file, 'r') as f:
                    existing_prompts = json.load(f)
                self.print_success(f"Found {len(existing_prompts)} existing custom prompts")
            except Exception as e:
                self.print_warning(f"Could not load existing prompts: {e}")

        self.print_info("You can now view default prompts before customizing them!")
        self.print_info("Each prompt can be viewed, used as-is, or customized to your needs.")

        prompt_choice = self.get_choice(
            "How would you like to configure prompts?",
            [
                "Use default prompts (recommended for first-time users)",
                "Use existing custom prompts" + (f" ({len(existing_prompts)} found)" if existing_prompts else ""),
                "Customize target executives (job titles to search for)",
                "Customize web search criteria (business relevance)",
                "Customize email template (contact outreach)"
            ],
            1
        )

        custom_prompts = {}

        if prompt_choice == 1:
            self.print_success("Using all default prompts")
            return
        elif prompt_choice == 2 and existing_prompts:
            self.print_success("Using existing custom prompts")
            custom_prompts = existing_prompts
        elif prompt_choice == 3:
            custom_prompts = self._customize_target_executives()
        elif prompt_choice == 4:
            custom_prompts = self._customize_web_search()
        elif prompt_choice == 5:
            custom_prompts = self._customize_email_template()

        if custom_prompts:
            # Save custom prompts
            try:
                self.custom_prompts_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.custom_prompts_file, 'w') as f:
                    json.dump(custom_prompts, f, indent=2)
                self.print_success(f"Saved {len(custom_prompts)} custom prompts")
                self._show_customization_summary(custom_prompts)
            except Exception as e:
                self.print_error(f"Could not save custom prompts: {e}")

    def _customize_target_executives(self) -> Dict[str, str]:
        """Customize target executive roles for LinkedIn search"""
        prompt_log(f"\n{Colors.BLUE}🎯 Target Executives Configuration{Colors.END}")
        prompt_log("Configure which executive roles to search for on LinkedIn")
        prompt_log("Current default: CEO, CTO, COO, Founder, VP Operations, Head of Supply Chain")

        custom_targets = self.get_input(
            "Enter target executive roles (comma-separated, or press Enter for default)",
            "CEO, CTO, COO, Founder, VP Operations, Head of Supply Chain"
        )

        if custom_targets and custom_targets != "CEO, CTO, COO, Founder, VP Operations, Head of Supply Chain":
            self.print_success(f"Target executives updated: {custom_targets}")
            return {"prospect_enricher_target_executives": custom_targets}
        else:
            self.print_info("Using default target executives")
            return {}

    def _customize_web_search(self) -> Dict[str, str]:
        """Customize web search criteria for business relevance"""
        prompt_log(f"\n{Colors.BLUE}🔍 Web Search Criteria Configuration{Colors.END}")
        prompt_log("Configure how the AI determines if a company is relevant for your business")
        prompt_log("Current default focuses on grocery and e-commerce relevance")

        custom_criteria = self.get_input(
            "Enter custom business relevance criteria (or press Enter for default)",
            "Companies in grocery retail, e-commerce, supply chain, or logistics"
        )

        if custom_criteria and custom_criteria != "Companies in grocery retail, e-commerce, supply chain, or logistics":
            self.print_success(f"Web search criteria updated")
            return {
                "web_enricher_user_prompt": f"Relevance Criteria: {custom_criteria}\n\nBegin your research now using the web search tool"}
        else:
            self.print_info("Using default web search criteria")
            return {}

    def _customize_email_template(self) -> Dict[str, str]:
        """Customize email template for contact outreach"""
        prompt_log(f"\n{Colors.BLUE}📧 Email Template Configuration{Colors.END}")
        prompt_log("Configure the email template used for outreach to prospects")
        prompt_log("This template will be used when creating HubSpot contacts")

        self.print_info("Current default creates professional outreach emails with:")
        self.print_info("- Personalized subject lines")
        self.print_info("- Company-specific value propositions")
        self.print_info("- Clear call-to-action")

        customize_choice = self.get_choice(
            "Do you want to customize the email template?",
            ["Keep default email template", "Enter custom email template"],
            1
        )

        if customize_choice == 2:
            custom_template = self.get_input(
                "Enter your custom email template (use {{company_name}}, {{contact_name}} for placeholders)"
            )

            if custom_template:
                self.print_success("Email template updated")
                return {"email_template": custom_template}

        self.print_info("Using default email template")
        return {}

    def _show_customization_summary(self, custom_prompts: Dict[str, str]):
        """Show summary of customized prompts"""
        prompt_log(f"\n{Colors.BLUE}📋 Customization Summary{Colors.END}")
        prompt_log("─" * 40)

        for key, value in custom_prompts.items():
            if key == "prospect_enricher_target_executives":
                readable_name = "Target Executives"
            elif key == "web_enricher_user_prompt":
                readable_name = "Web Search Criteria"
            elif key == "email_template":
                readable_name = "Email Template"
            else:
                readable_name = key.replace("_", " ").title()

            prompt_log(f"{Colors.GREEN}✏️ {readable_name}: {len(value)} characters{Colors.END}")

        prompt_log("─" * 40)

    def save_env_file(self):
        """Save configuration to .env file"""
        try:
            with open(self.env_file_path, 'w') as f:
                f.write(f"# AI SDR Agent Orchestrated Configuration\n")
                f.write(f"# Generated on {datetime.now().isoformat()}\n\n")

                for key, value in self.config.items():
                    f.write(f'{key}="{value}"\n')

            self.print_success(f"Configuration saved to {self.env_file_path}")
        except Exception as e:
            self.print_error(f"Could not save configuration: {e}")
            return False
        return True

    def show_configuration_summary(self):
        """Show configuration summary"""
        self.print_section("Configuration Summary")

        prompt_log(f"{Colors.BLUE}Workflow Type: 🔄 Orchestrated (Per-Company){Colors.END}")

        prompt_log(f"\n{Colors.BLUE}API Configuration:{Colors.END}")
        prompt_log(f"  OpenAI API: {'✅ Configured' if self.config.get('OPENAI_API_KEY') else '❌ Missing'}")
        prompt_log(f"  HubSpot API: {'✅ Configured' if self.config.get('HUBSPOT_API_KEY') else '⚠️  Not configured'}")

        prompt_log(f"\n{Colors.BLUE}Data Source:{Colors.END}")
        prompt_log(f"  Type: {self.config.get('DATA_SOURCE_TYPE', 'Not set')}")
        if self.config.get('CSV_FILE_PATH'):
            prompt_log(f"  File: {self.config['CSV_FILE_PATH']}")
        if self.config.get('GOOGLE_SHEET_URL'):
            prompt_log(f"  Sheet: {self.config['GOOGLE_SHEET_URL']}")

        prompt_log(f"\n{Colors.BLUE}Processing Options:{Colors.END}")
        prompt_log(f"  Max Companies: {self.config.get('MAX_COMPANIES', 'Not set')}")
        prompt_log(f"  Browser Timeout: {self.config.get('BROWSER_TIMEOUT', 'Not set')}s")
        prompt_log(f"  Create HubSpot Contacts: {self.config.get('CREATE_HUBSPOT_CONTACTS', 'Not set')}")

        if self.config.get('PARALLEL_PROCESSING') == 'true':
            prompt_log(f"  Parallel Processing: ✅ Enabled")
            prompt_log(f"  Max Workers: {self.config.get('MAX_WORKERS', 'Not set')}")
        else:
            prompt_log(f"  Parallel Processing: ❌ Disabled (Sequential)")

        if self.custom_prompts_file.exists():
            prompt_log(f"\n{Colors.BLUE}Custom Prompts: ✅ Configured{Colors.END}")

    def run_workflow_menu(self):
        """Show workflow execution options"""
        self.print_section("Orchestrated Workflow Execution")

        self.print_info("The orchestrated workflow processes each company individually.")
        self.print_info("This provides better error isolation and progress tracking.")

        choice = self.get_choice(
            "What would you like to do?",
            [
                "Run the orchestrated SDR workflow",
                "Run with progress monitoring (shows company-by-company progress)",
                "Validate data models first",
                "Compare with monolithic workflow",
                "Exit"
            ],
            1
        )

        if choice == 1:
            return "run_orchestrated"
        elif choice == 2:
            return "run_with_monitoring"
        elif choice == 3:
            return "validate_models"
        elif choice == 4:
            return "compare_workflows"
        else:
            return "exit"

    async def run_orchestrated_workflow(self, with_monitoring: bool = False):
        """Run the orchestrated SDR workflow"""
        self.print_section("Running Orchestrated SDR Workflow")
        self.print_info("Starting the per-company orchestrated workflow...")

        if with_monitoring:
            self.print_info("Progress monitoring enabled - you'll see updates for each company")

        try:
            # Ensure custom prompts file exists to prevent duplicate prompts
            if self.custom_prompts_file.exists():
                self.print_info(f"Using custom prompts from {self.custom_prompts_file}")
            else:
                # Create empty custom prompts file to signal we've already configured prompts
                self.custom_prompts_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.custom_prompts_file, 'w') as f:
                    json.dump({}, f)  # Empty dict means use defaults
                self.print_info("Using default prompts")

            # Run the orchestrated workflow with CLI configuration
            await run_orchestrated_workflow(self.config)
            self.print_success("Orchestrated workflow completed successfully!")

        except KeyboardInterrupt:
            self.print_warning("Workflow interrupted by user")
        except Exception as e:
            self.print_error(f"Workflow failed: {e}")

    def run_model_validation(self):
        """Run model validation"""
        self.print_section("Model Validation")
        self.print_info("Validating Pydantic models...")

        try:
            validate_models()
            self.print_success("Model validation completed successfully!")
        except Exception as e:
            self.print_error(f"Model validation failed: {e}")

    def compare_workflows(self):
        """Show comparison between monolithic and orchestrated workflows"""
        self.print_section("Workflow Comparison")

        prompt_log(f"\n{Colors.BLUE}🔄 Monolithic Workflow:{Colors.END}")
        prompt_log("  • Processes all companies in a single run")
        prompt_log("  • State maintained across entire workflow")
        prompt_log("  • Single point of failure affects all companies")
        prompt_log("  • Lower overhead, faster for small datasets")

        prompt_log(f"\n{Colors.BLUE}🔄 Orchestrated Workflow:{Colors.END}")
        prompt_log("  • Processes companies individually")
        prompt_log("  • Isolated state per company")
        prompt_log("  • Failures don't affect other companies")
        prompt_log("  • Better progress tracking and resumability")
        prompt_log("  • Can be parallelized for faster execution")

        prompt_log(f"\n{Colors.YELLOW}Recommendation:{Colors.END}")
        prompt_log("  • Use orchestrated for production workloads")
        prompt_log("  • Use monolithic for testing or small datasets")

    async def run(self):
        """Main application loop"""
        self.print_header()

        # Check existing configuration
        existing_config = self.check_existing_env()

        # Configuration menu
        if existing_config:
            use_existing = self.get_choice(
                "Found existing configuration. What would you like to do?",
                [
                    "Use existing configuration and run orchestrated workflow",
                    "Reconfigure settings",
                    "Exit"
                ],
                1
            )

            if use_existing == 1:
                self.config = existing_config
                self.show_configuration_summary()
            elif use_existing == 3:
                prompt_log(f"{Colors.YELLOW}Goodbye!{Colors.END}")
                return

        # If no existing config or user wants to reconfigure
        if not self.config:
            self.configure_api_keys(existing_config)
            await self.configure_data_source(existing_config)
            if self.config.get("DATA_SOURCE_TYPE") == "mongo":
                await self.claim_and_run_mongo_campaigns()
                return
            self.show_configuration_summary()

            self.configure_processing_options(existing_config)
            self.configure_prompts()

            # Save configuration
            if not self.save_env_file():
                prompt_log(f"{Colors.RED}Failed to save configuration. Exiting.{Colors.END}")
                return
            while True:
                action = self.run_workflow_menu()
                if action == "run_orchestrated":
                    await self.run_orchestrated_workflow(with_monitoring=False)
                elif action == "run_with_monitoring":
                    await self.run_orchestrated_workflow(with_monitoring=True)
                elif action == "validate_models":
                    self.run_model_validation()
                elif action == "compare_workflows":
                    self.compare_workflows()
                elif action == "exit":
                    break
            return

            self.show_configuration_summary()

        # Workflow execution loop
        while True:
            action = self.run_workflow_menu()

            if action == "run_orchestrated":
                await self.run_orchestrated_workflow(with_monitoring=False)
            elif action == "run_with_monitoring":
                await self.run_orchestrated_workflow(with_monitoring=True)
            elif action == "validate_models":
                self.run_model_validation()
            elif action == "compare_workflows":
                self.compare_workflows()
            elif action == "exit":
                break

        prompt_log(f"\n{Colors.GREEN}Thank you for using AI SDR Agent Orchestrated! 🤖{Colors.END}")


def main():
    """Main entry point"""
    try:
        app = OrchestratedCLIApp()
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Configuration interrupted. Goodbye!{Colors.END}")
    except Exception as e:
        log, prompt_log = setup_basic_logging()
        prompt_log(f"❌ Unexpected error: {e}")
        import traceback
        prompt_log(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
