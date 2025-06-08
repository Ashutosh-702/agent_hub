#!/usr/bin/env python3
"""
AI SDR Agent - Interactive CLI Application

User-friendly command line interface with guided configuration for the AI SDR workflow.
This is the main CLI entry point for the AI SDR agent.
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_basic_logging():
    """Setup basic logging for launcher errors"""
    try:
        from sdr.logging_config import clean_log, prompt_log
        return clean_log, prompt_log
    except ImportError:
        # Fallback to print if logging not available
        fallback = lambda msg, level="info": print(f"[{level.upper()}] {msg}")
        return fallback, print

try:
    from sdr.main import main as run_workflow
    from sdr.validate_models import main as validate_models
    from sdr.logging_config import clean_log, prompt_log
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


class CLIApp:
    """Interactive CLI application for AI SDR workflow configuration"""

    def __init__(self):
        self.config = {}
        current_dir = Path(__file__).parent
        self.env_file_path = current_dir / ".env"
        self.custom_prompts_file = current_dir / "sdr" / "config" / "custom_prompts.json"
        
    def print_header(self):
        """Print application header"""
        prompt_log(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
        prompt_log(f"{Colors.BOLD}{Colors.BLUE}🤖 AI SDR Agent - Interactive Configuration{Colors.END}")
        prompt_log(f"{Colors.CYAN}{'='*70}{Colors.END}")
        prompt_log(f"{Colors.YELLOW}Welcome to the AI SDR prospect research and enrichment tool!{Colors.END}")
        prompt_log(f"{Colors.YELLOW}This wizard will guide you through the setup process.{Colors.END}\n")

    def print_section(self, title: str):
        """Print section header"""
        prompt_log(f"\n{Colors.CYAN}{'─'*50}{Colors.END}")
        prompt_log(f"{Colors.BOLD}{Colors.BLUE}📋 {title}{Colors.END}")
        prompt_log(f"{Colors.CYAN}{'─'*50}{Colors.END}")

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

    def configure_data_source(self, existing_config: Dict[str, str]):
        """Configure data source settings"""
        self.print_section("Data Source Configuration")
        
        # Data source type
        current_type = existing_config.get("DATA_SOURCE_TYPE", "csv")
        source_choice = self.get_choice(
            "Select your data source type:",
            ["CSV file", "Excel file", "Google Sheet"],
            1 if current_type == "csv" else 2 if current_type == "excel" else 3
        )
        
        if source_choice == 1:
            self.config["DATA_SOURCE_TYPE"] = "csv"
        elif source_choice == 2:
            self.config["DATA_SOURCE_TYPE"] = "excel"
        else:
            self.config["DATA_SOURCE_TYPE"] = "google_sheet"
        
        # File path or Google Sheet URL
        if self.config["DATA_SOURCE_TYPE"] in ["csv", "excel"]:
            current_path = existing_config.get("CSV_FILE_PATH", "companies.csv")
            self.config["CSV_FILE_PATH"] = self.get_input(
                f"Enter path to your {self.config['DATA_SOURCE_TYPE'].upper()} file",
                current_path
            )
        else:
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

    def configure_processing_options(self, existing_config: Dict[str, str]):
        """Configure processing options"""
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
                "Interactive prompt customization (view defaults first)",
                "View all default prompts (read-only)",
                "Quick customize LinkedIn research only",
                "Quick customize web research only", 
                "Quick customize HubSpot integration only",
                "Advanced: Customize all prompts with preview"
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
            custom_prompts = self._interactive_prompt_customization()
        elif prompt_choice == 4:
            self._display_all_defaults()
            return
        elif prompt_choice == 5:
            custom_prompts = self._customize_linkedin_prompts()
        elif prompt_choice == 6:
            custom_prompts = self._customize_web_prompts()
        elif prompt_choice == 7:
            custom_prompts = self._customize_hubspot_prompts()
        elif prompt_choice == 8:
            custom_prompts = self._customize_all_prompts_advanced()
        
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

    def _interactive_prompt_customization(self) -> Dict[str, str]:
        """Interactive prompt customization with default viewing"""
        prompt_log(f"\n{Colors.BLUE}🎯 Interactive Prompt Customization{Colors.END}")
        prompt_log("You can view each default prompt before deciding to customize it.")
        
        from sdr.prompts import get_user_prompts
        return get_user_prompts()

    def _display_all_defaults(self):
        """Display all default prompts for reference"""
        prompt_log(f"\n{Colors.BLUE}📚 All Default Prompts Reference{Colors.END}")
        prompt_log("─" * 60)
        
        from sdr.prompts import DEFAULT_PROMPTS
        
        prompt_categories = {
            "LinkedIn Research": [
                ("prospect_enricher_instructions", "LinkedIn Research Instructions"),
                ("prospect_enricher_user_prompt", "LinkedIn User Prompt Template"),
            ],
            "Web Research": [
                ("web_enricher_system_prompt", "Web Research System Prompt"),
                ("web_enricher_user_prompt", "Web Research User Prompt")
            ],
            "HubSpot Integration": [
                ("hubspot_creator_instructions", "HubSpot Contact Creation Instructions"),
                ("hubspot_creator_user_prompt", "HubSpot User Prompt Template")
            ]
        }
        
        for category, prompts in prompt_categories.items():
            prompt_log(f"\n{Colors.CYAN}🏷️ {category}{Colors.END}")
            prompt_log("─" * 40)
            
            for key, name in prompts:
                prompt_content = DEFAULT_PROMPTS.get(key, "No default available")
                prompt_log(f"\n{Colors.YELLOW}📝 {name}:{Colors.END}")
                
                # Show first 300 characters
                if len(prompt_content) > 5000:
                    preview = prompt_content[:5000] + "..."
                else:
                    preview = prompt_content
                
                prompt_log(f"   {preview}")
                prompt_log(f"   {Colors.BLUE}📊 Length: {len(prompt_content)} characters{Colors.END}")
        
        prompt_log(f"\n{Colors.GREEN}💡 Use option 3 or 8 to customize any of these prompts{Colors.END}")

    def _show_customization_summary(self, custom_prompts: Dict[str, str]):
        """Show summary of customized prompts"""
        prompt_log(f"\n{Colors.BLUE}📋 Customization Summary{Colors.END}")
        prompt_log("─" * 40)
        
        for key, value in custom_prompts.items():
            readable_name = key.replace("_", " ").title()
            prompt_log(f"{Colors.GREEN}✏️ {readable_name}: {len(value)} characters{Colors.END}")
        
        prompt_log("─" * 40)

    def _customize_all_prompts_advanced(self) -> Dict[str, str]:
        """Advanced customization with preview for all prompts"""
        prompt_log(f"\n{Colors.BLUE}🔧 Advanced Prompt Customization{Colors.END}")
        prompt_log("You'll be able to view and customize each prompt individually.")

        all_prompts = [
            ("prospect_enricher_instructions", "LinkedIn Research Instructions"),
            ("prospect_enricher_user_prompt", "LinkedIn User Prompt Template"),
            ("web_enricher_system_prompt", "Web Research System Prompt"),
            ("web_enricher_user_prompt", "Web Research User Prompt"),
            ("hubspot_creator_instructions", "HubSpot Contact Creation Instructions"),
            ("hubspot_creator_user_prompt", "HubSpot User Prompt Template"),
            ("prospect_enricher_target_executives", "Target Executives List")
        ]
        
        custom_prompts = {}
        
        for key, name in all_prompts:
            if self._should_customize_prompt(key, name):
                custom_prompt = self._get_custom_prompt_with_preview(key, name)
                if custom_prompt:
                    custom_prompts[key] = custom_prompt
        
        return custom_prompts

    def _should_customize_prompt(self, key: str, name: str) -> bool:
        """Ask if user wants to customize this specific prompt"""
        choice = self.get_choice(
            f"Do you want to customize: {name}?",
            ["Yes, customize this prompt", "Skip this prompt"],
            2
        )
        return choice == 1

    def _get_custom_prompt_with_preview(self, key: str, name: str) -> str:
        """Get custom prompt with option to view default first"""
        from sdr.prompts import DEFAULT_PROMPTS
        
        prompt_log(f"\n{Colors.CYAN}📝 Customizing: {name}{Colors.END}")
        
        default_prompt = DEFAULT_PROMPTS.get(key, "No default available")
        
        view_choice = self.get_choice(
            "What would you like to do?",
            ["View default prompt first", "Enter custom prompt directly", "Skip this prompt"],
            1
        )
        
        if view_choice == 1:
            # Show default prompt
            prompt_log(f"\n{Colors.BLUE}📋 Default Prompt for {name}:{Colors.END}")
            prompt_log("═" * 60)
            
            if len(default_prompt) > 1000:
                prompt_log(default_prompt[:1000] + "\n\n[... truncated for display ...]")
                prompt_log(f"\n{Colors.YELLOW}📊 Full length: {len(default_prompt)} characters{Colors.END}")
            else:
                prompt_log(default_prompt)
            
            prompt_log("═" * 60)
            
            # After viewing, ask what to do
            follow_up = self.get_choice(
                "After viewing the default, what would you like to do?",
                ["Use this default (no changes)", "Enter a custom prompt", "Skip this prompt"],
                1
            )
            
            if follow_up == 1:
                return ""  # Use default
            elif follow_up == 3:
                return ""  # Skip
            # If 2, continue to custom input below
        
        elif view_choice == 3:
            return ""  # Skip
        
        # Get custom prompt input
        prompt_log(f"\n{Colors.YELLOW}✏️ Enter custom prompt for {name}:{Colors.END}")
        prompt_log("💡 Tips:")
        prompt_log("   • Be specific and clear in your instructions")
        prompt_log("   • Include any special formatting requirements")
        prompt_log("   • Press Enter on an empty line to finish")
        prompt_log("   • Type 'DEFAULT' to use the default prompt")
        
        custom_prompt = input(f"\nCustom prompt for {name}: ").strip()
        
        if custom_prompt.upper() == "DEFAULT" or not custom_prompt:
            return ""
        
        prompt_log(f"{Colors.GREEN}✅ Custom prompt set ({len(custom_prompt)} characters){Colors.END}")
        return custom_prompt

    def _customize_linkedin_prompts(self) -> Dict[str, str]:
        """Customize LinkedIn research prompts"""
        prompt_log(f"\n{Colors.BLUE}LinkedIn Research Configuration:{Colors.END}")
        prompt_log("Current default searches for executives and collects LinkedIn profile URLs")
        prompt_log("You can customize the target roles and search instructions")
        
        custom_targets = self.get_input(
            "Enter target executive roles (comma-separated, or press Enter for default)",
            "CEO, CTO, COO, Founder, VP Operations, Head of Supply Chain"
        )
        
        if custom_targets:
            return {"prospect_enricher_target_executives": custom_targets}
        return {}

    def _customize_web_prompts(self) -> Dict[str, str]:
        """Customize web research prompts"""
        prompt_log(f"\n{Colors.BLUE}Web Research Configuration:{Colors.END}")
        prompt_log("Current default focuses on grocery and e-commerce relevance")
        prompt_log("You can customize the business criteria and research focus")
        
        custom_criteria = self.get_input(
            "Enter custom business relevance criteria (or press Enter for default)"
        )
        
        if custom_criteria:
            return {"web_enricher_user_prompt": f"Relevance Criteria: {custom_criteria}\n\nBegin your research now using the web search tool"}
        return {}

    def _customize_hubspot_prompts(self) -> Dict[str, str]:
        """Customize HubSpot integration prompts"""
        prompt_log(f"\n{Colors.BLUE}HubSpot Integration Configuration:{Colors.END}")
        prompt_log("Current default creates contacts with standard field mapping")
        prompt_log("You can customize the field mapping and creation logic")
        
        custom_mapping = self.get_input(
            "Enter custom field mapping instructions (or press Enter for default)"
        )
        
        if custom_mapping:
            return {"hubspot_creator_instructions": custom_mapping}
        return {}

    def _customize_all_prompts(self) -> Dict[str, str]:
        """Customize all prompts interactively"""
        custom_prompts = {}
        
        # LinkedIn
        linkedin_prompts = self._customize_linkedin_prompts()
        custom_prompts.update(linkedin_prompts)
        
        # Web research
        web_prompts = self._customize_web_prompts()
        custom_prompts.update(web_prompts)
        
        # HubSpot
        hubspot_prompts = self._customize_hubspot_prompts()
        custom_prompts.update(hubspot_prompts)
        
        return custom_prompts

    def save_env_file(self):
        """Save configuration to .env file"""
        try:
            with open(self.env_file_path, 'w') as f:
                f.write(f"# AI SDR Agent Configuration\n")
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
        
        prompt_log(f"{Colors.BLUE}API Configuration:{Colors.END}")
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
        
        if self.custom_prompts_file.exists():
            prompt_log(f"\n{Colors.BLUE}Custom Prompts: ✅ Configured{Colors.END}")

    def run_workflow_menu(self):
        """Show workflow execution options"""
        self.print_section("Workflow Execution")
        
        choice = self.get_choice(
            "What would you like to do?",
            [
                "Run the complete SDR workflow",
                "Validate data models first",
                "Open GUI application",
                "Exit"
            ],
            1
        )
        
        if choice == 1:
            return "run_workflow"
        elif choice == 2:
            return "validate_models"
        elif choice == 3:
            return "open_gui"
        else:
            return "exit"

    async def run_complete_workflow(self):
        """Run the complete SDR workflow"""
        self.print_section("Running SDR Workflow")
        self.print_info("Starting the complete prospect research and enrichment workflow...")
        
        try:
            # Set environment variables from config
            for key, value in self.config.items():
                os.environ[key] = str(value)
            
            # Run the main workflow
            await run_workflow()
            self.print_success("Workflow completed successfully!")
            
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

    def open_gui_application(self):
        """Open GUI application"""
        self.print_section("Opening GUI Application")
        self.print_info("Launching the GUI interface...")
        
        try:
            import subprocess
            subprocess.run([sys.executable, str(current_dir / "run_gui.py")])
        except Exception as e:
            self.print_error(f"Could not launch GUI: {e}")

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
                    "Use existing configuration and run workflow",
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
            self.configure_data_source(existing_config)
            self.configure_processing_options(existing_config)
            self.configure_prompts()
            
            # Save configuration
            if not self.save_env_file():
                prompt_log(f"{Colors.RED}Failed to save configuration. Exiting.{Colors.END}")
                return
            
            self.show_configuration_summary()
        
        # Workflow execution loop
        while True:
            action = self.run_workflow_menu()
            
            if action == "run_workflow":
                await self.run_complete_workflow()
            elif action == "validate_models":
                self.run_model_validation()
            elif action == "open_gui":
                self.open_gui_application()
            elif action == "exit":
                break
        
        prompt_log(f"\n{Colors.GREEN}Thank you for using AI SDR Agent! 🤖{Colors.END}")


def main():
    """Main entry point"""
    try:
        app = CLIApp()
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