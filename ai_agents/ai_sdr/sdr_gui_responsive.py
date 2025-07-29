#!/usr/bin/env python3
"""
Advanced SDR Workflow GUI - Responsive Version

An improved Qt-based interface with better responsive design for small windows.
Key improvements:
- Better layout management for small screens
- Minimum sizes for critical elements
- Collapsible sections for space optimization
- Improved text field sizing
- Real-time log monitoring
- Results viewing
"""

import asyncio
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import os
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSettings, pyqtSlot
)
from PyQt6.QtGui import (
    QFont, QTextCursor, QAction
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QGridLayout, QFormLayout, QProgressBar, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QScrollArea, QDialog
)
# Import your SDR modules
from dotenv import load_dotenv, set_key

from ai_agents.ai_sdr.sdr.logging_config import unregister_gui_callback, get_log_file_path
from ai_agents.ai_sdr.sdr.main import create_run_directories
from ai_agents.ai_sdr.sdr.prompts import load_prompts_from_file, save_prompts_to_file, DEFAULT_PROMPTS
from ai_agents.ai_sdr.sdr.main import main as wf_main
from ai_agents.ai_sdr.sdr.logging_config import clear_all_gui_callbacks, register_gui_callback


class QtLogHandler:
    """Custom log handler that emits Qt signals for real-time GUI updates"""

    def __init__(self, signal_emitter):
        self.signal_emitter = signal_emitter

    def write(self, message):
        if message.strip():  # Only emit non-empty messages
            self.signal_emitter.emit(message.strip())


class CollapsibleGroupBox(QGroupBox):
    """A QGroupBox that can be collapsed/expanded to save space"""

    def __init__(self, title="", parent=None):
        super(CollapsibleGroupBox, self).__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self._on_toggled)
        # Fix black background issue
        self.setStyleSheet("""
            CollapsibleGroupBox {
                background-color: #ffffff;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            CollapsibleGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                background-color: #ffffff;
                color: #1f2937;
            }
            CollapsibleGroupBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background-color: #ffffff;
            }
            CollapsibleGroupBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
        """)

    def _on_toggled(self, checked):
        self.setVisible(checked)
        if not checked:
            self.setMaximumHeight(30)
        else:
            self.setMaximumHeight(16777215)


class ResponsiveConfigurationTab(QWidget):
    """Configuration tab with responsive design for small windows"""

    def __init__(self):
        super(ResponsiveConfigurationTab, self).__init__()
        self.settings = QSettings('SDR_Workflow', 'Configuration')
        self.init_ui()
        self.create_default_env_if_missing()
        self.load_settings()

    def init_ui(self):
        # Main scroll area for the entire tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # API Configuration - Collapsible
        api_group = CollapsibleGroupBox("🔑 API Configuration")
        api_layout = QVBoxLayout()
        api_layout.setSpacing(12)

        # OpenAI API Key
        openai_container = self._create_field_container(
            "OpenAI API Key*:",
            "Your OpenAI API key for AI-powered analysis"
        )
        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key.setPlaceholderText("sk-...")
        self.openai_key.setMinimumWidth(200)
        openai_container.layout().addWidget(self.openai_key)
        api_layout.addWidget(openai_container)

        # HubSpot API Key
        hubspot_container = self._create_field_container(
            "HubSpot API Key:",
            "Optional - For automatic contact creation"
        )
        self.hubspot_key = QLineEdit()
        self.hubspot_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.hubspot_key.setPlaceholderText("Optional")
        self.hubspot_key.setMinimumWidth(200)
        hubspot_container.layout().addWidget(self.hubspot_key)
        api_layout.addWidget(hubspot_container)

        # Clearbit API Key
        clearbit_container = self._create_field_container(
            "Clearbit API Key:",
            "Optional - For company enrichment"
        )
        self.clearbit_key = QLineEdit()
        self.clearbit_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.clearbit_key.setPlaceholderText("Optional")
        self.clearbit_key.setMinimumWidth(200)
        clearbit_container.layout().addWidget(self.clearbit_key)
        api_layout.addWidget(clearbit_container)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # Data Source Configuration - Collapsible
        data_group = CollapsibleGroupBox("📊 Data Source Configuration")
        data_layout = QVBoxLayout()
        data_layout.setSpacing(12)

        # Data Source Type
        type_container = self._create_field_container(
            "Data Source Type:",
            "Choose your input data format"
        )
        self.data_source_type = QComboBox()
        self.data_source_type.addItems(["csv", "google_sheets"])
        self.data_source_type.currentTextChanged.connect(self.on_data_source_changed)
        self.data_source_type.setMinimumWidth(200)
        type_container.layout().addWidget(self.data_source_type)
        data_layout.addWidget(type_container)

        # CSV Configuration
        self.csv_widget = QWidget()
        csv_layout = QVBoxLayout()
        csv_layout.setContentsMargins(0, 0, 0, 0)

        csv_container = self._create_field_container(
            "CSV File Path:",
            "Path to your companies CSV file"
        )
        csv_input_layout = QHBoxLayout()
        csv_input_layout.setSpacing(8)
        self.csv_file_path = QLineEdit()
        self.csv_file_path.setPlaceholderText("ai_agents/data/company_names.csv")
        self.csv_file_path.setMinimumWidth(150)
        csv_browse_btn = QPushButton("Browse")
        csv_browse_btn.clicked.connect(self.browse_csv_file)
        csv_browse_btn.setMaximumWidth(80)
        csv_input_layout.addWidget(self.csv_file_path, 1)
        csv_input_layout.addWidget(csv_browse_btn, 0)
        csv_container.layout().addLayout(csv_input_layout)
        csv_layout.addWidget(csv_container)
        self.csv_widget.setLayout(csv_layout)
        data_layout.addWidget(self.csv_widget)

        # Google Sheets Configuration
        self.sheets_widget = QWidget()
        sheets_layout = QVBoxLayout()
        sheets_layout.setContentsMargins(0, 0, 0, 0)
        sheets_layout.setSpacing(12)

        # URL field
        url_container = self._create_field_container(
            "Google Sheet URL:",
            "Full URL to your Google Sheet"
        )
        self.sheet_url = QLineEdit()
        self.sheet_url.setPlaceholderText("https://docs.google.com/spreadsheets/d/...")
        self.sheet_url.setMinimumWidth(200)
        url_container.layout().addWidget(self.sheet_url)
        sheets_layout.addWidget(url_container)

        # Worksheet field
        worksheet_container = self._create_field_container(
            "Worksheet Name:",
            "Name of the worksheet tab"
        )
        self.worksheet_name = QLineEdit()
        self.worksheet_name.setPlaceholderText("Sheet1")
        self.worksheet_name.setMinimumWidth(200)
        worksheet_container.layout().addWidget(self.worksheet_name)
        sheets_layout.addWidget(worksheet_container)

        self.sheets_widget.setLayout(sheets_layout)
        data_layout.addWidget(self.sheets_widget)

        data_group.setLayout(data_layout)
        layout.addWidget(data_group)

        # Processing Configuration - Collapsible
        process_group = CollapsibleGroupBox("⚙️ Processing Configuration")
        process_layout = QVBoxLayout()
        process_layout.setSpacing(12)

        # Max Companies
        max_companies_container = self._create_field_container(
            "Max Companies:",
            "Maximum number of companies to process"
        )
        self.max_companies = QSpinBox()
        self.max_companies.setRange(1, 1000)
        self.max_companies.setValue(100)
        self.max_companies.setMinimumWidth(120)
        self.max_companies.setMaximumWidth(200)
        max_companies_container.layout().addWidget(self.max_companies)
        process_layout.addWidget(max_companies_container)

        # Browser Timeout
        timeout_container = self._create_field_container(
            "Browser Timeout:",
            "Timeout for browser operations (seconds)"
        )
        self.browser_timeout = QSpinBox()
        self.browser_timeout.setRange(10, 120)
        self.browser_timeout.setValue(30)
        self.browser_timeout.setSuffix(" seconds")
        self.browser_timeout.setMinimumWidth(120)
        self.browser_timeout.setMaximumWidth(200)
        timeout_container.layout().addWidget(self.browser_timeout)
        process_layout.addWidget(timeout_container)

        process_group.setLayout(process_layout)
        layout.addWidget(process_group)

        # HubSpot Configuration - Collapsible
        hubspot_group = CollapsibleGroupBox("🚀 HubSpot Configuration")
        hubspot_layout = QVBoxLayout()
        hubspot_layout.setSpacing(12)

        # Create HubSpot Contacts
        create_contacts_container = QWidget()
        create_contacts_layout = QHBoxLayout()
        create_contacts_layout.setContentsMargins(0, 0, 0, 0)
        self.create_hubspot_contacts = QCheckBox("Create HubSpot Contacts")
        self.create_hubspot_contacts.setChecked(True)
        create_contacts_layout.addWidget(self.create_hubspot_contacts)
        create_contacts_layout.addStretch()
        create_contacts_container.setLayout(create_contacts_layout)
        hubspot_layout.addWidget(create_contacts_container)

        # HubSpot Owner Email
        owner_container = self._create_field_container(
            "HubSpot Owner Email:",
            "Email for contact assignment"
        )
        self.hubspot_owner_email = QLineEdit()
        self.hubspot_owner_email.setPlaceholderText("your-email@company.com")
        self.hubspot_owner_email.setMinimumWidth(200)
        owner_container.layout().addWidget(self.hubspot_owner_email)
        hubspot_layout.addWidget(owner_container)

        hubspot_group.setLayout(hubspot_layout)
        layout.addWidget(hubspot_group)

        # Buttons - Fixed at bottom
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 20, 0, 0)

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setMinimumHeight(36)

        load_btn = QPushButton("Load from .env")
        load_btn.clicked.connect(self.load_from_env)
        load_btn.setProperty("class", "secondary")
        load_btn.setMinimumHeight(36)

        test_btn = QPushButton("Test Configuration")
        test_btn.clicked.connect(self.test_configuration)
        test_btn.setProperty("class", "secondary")
        test_btn.setMinimumHeight(36)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        reset_btn.setProperty("class", "danger")
        reset_btn.setMinimumHeight(36)
        reset_btn.setToolTip("Clear all fields and reset to default values")

        button_layout.addWidget(save_btn)
        button_layout.addWidget(load_btn)
        button_layout.addWidget(test_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_container.setLayout(button_layout)
        layout.addWidget(button_container)

        # Add stretch at the end
        layout.addStretch()

        # Set the content widget
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        # Initial setup
        self.on_data_source_changed()

    def create_default_env_if_missing(self):
        """Create default .env file if it doesn't exist"""
        current_dir = Path(__file__).parent
        env_path = current_dir / ".env"

        if not env_path.exists():
            default_env_content = """# AI SDR Agent Configuration
# Required API Keys
OPENAI_API_KEY=your-openai-api-key-here

# Optional API Keys
HUBSPOT_API_KEY=your-hubspot-api-key-here
CLEARBIT_API_KEY=your-clearbit-api-key-here

# Data Source Configuration
DATA_SOURCE_TYPE=csv
CSV_FILE_PATH=ai_agents/data/company_names.csv
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/your-sheet-id/edit
GOOGLE_WORKSHEET_NAME=Sheet1

# Processing Configuration
MAX_COMPANIES=100
BROWSER_TIMEOUT=30

# HubSpot Configuration
CREATE_HUBSPOT_CONTACTS=true
HUBSPOT_OWNER_EMAIL=your-email@company.com
"""
            try:
                with open(env_path, 'w') as f:
                    f.write(default_env_content)
                print(f"Created default .env file at {env_path}")
            except Exception as e:
                print(f"Failed to create default .env file: {e}")

    def _create_field_container(self, label_text: str, help_text: str = "") -> QWidget:
        """Create a container for a form field with label and optional help text"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Label
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: 500; color: #374151;")
        layout.addWidget(label)

        # Help text
        if help_text:
            help_label = QLabel(help_text)
            help_label.setStyleSheet("font-size: 12px; color: #6b7280;")
            help_label.setWordWrap(True)
            layout.addWidget(help_label)

        container.setLayout(layout)
        return container

    def on_data_source_changed(self):
        """Handle data source type change"""
        is_csv = self.data_source_type.currentText() == "csv"
        self.csv_widget.setVisible(is_csv)
        self.sheets_widget.setVisible(not is_csv)

    def browse_csv_file(self):
        """Browse for CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.csv_file_path.setText(file_path)

    def save_settings(self):
        """Save configuration to QSettings and .env file"""
        try:
            # Save to QSettings
            self.settings.setValue("openai_key", self.openai_key.text())
            self.settings.setValue("hubspot_key", self.hubspot_key.text())
            self.settings.setValue("clearbit_key", self.clearbit_key.text())
            self.settings.setValue("data_source_type", self.data_source_type.currentText())
            self.settings.setValue("csv_file_path", self.csv_file_path.text())
            self.settings.setValue("sheet_url", self.sheet_url.text())
            self.settings.setValue("worksheet_name", self.worksheet_name.text())
            self.settings.setValue("max_companies", self.max_companies.value())
            self.settings.setValue("browser_timeout", self.browser_timeout.value())
            self.settings.setValue("create_hubspot_contacts", self.create_hubspot_contacts.isChecked())
            self.settings.setValue("hubspot_owner_email", self.hubspot_owner_email.text())

            # Save to .env file
            env_path = Path(".env")

            env_vars = {
                "OPENAI_API_KEY": self.openai_key.text(),
                "HUBSPOT_API_KEY": self.hubspot_key.text(),
                "CLEARBIT_API_KEY": self.clearbit_key.text(),
                "DATA_SOURCE_TYPE": self.data_source_type.currentText(),
                "CSV_FILE_PATH": self.csv_file_path.text(),
                "GOOGLE_SHEET_URL": self.sheet_url.text(),
                "GOOGLE_WORKSHEET_NAME": self.worksheet_name.text(),
                "MAX_COMPANIES": str(self.max_companies.value()),
                "BROWSER_TIMEOUT": str(self.browser_timeout.value()),
                "CREATE_HUBSPOT_CONTACTS": str(self.create_hubspot_contacts.isChecked()).lower(),
                "HUBSPOT_OWNER_EMAIL": self.hubspot_owner_email.text(),
            }

            for key, value in env_vars.items():
                if value:  # Only save non-empty values
                    set_key(env_path, key, value)

            QMessageBox.information(self, "Success", "Configuration saved successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    def load_settings(self):
        """Load configuration from QSettings, fallback to .env file"""
        # First check if QSettings has values, if not try .env file
        if not self.settings.value("openai_key", ""):
            self.load_from_env_if_exists()
        
        self.openai_key.setText(self.settings.value("openai_key", ""))
        self.hubspot_key.setText(self.settings.value("hubspot_key", ""))
        self.clearbit_key.setText(self.settings.value("clearbit_key", ""))
        self.data_source_type.setCurrentText(self.settings.value("data_source_type", "csv"))
        self.csv_file_path.setText(self.settings.value("csv_file_path", "ai_agents/data/company_names.csv"))
        self.sheet_url.setText(self.settings.value("sheet_url", ""))
        self.worksheet_name.setText(self.settings.value("worksheet_name", "Sheet1"))
        self.max_companies.setValue(int(self.settings.value("max_companies", 100)))
        self.browser_timeout.setValue(int(self.settings.value("browser_timeout", 30)))
        self.create_hubspot_contacts.setChecked(self.settings.value("create_hubspot_contacts", True, type=bool))
        self.hubspot_owner_email.setText(self.settings.value("hubspot_owner_email", ""))

        self.on_data_source_changed()

    def load_from_env_if_exists(self):
        """Silently load from .env file if it exists"""
        current_dir = Path(__file__).parent
        env_path = current_dir / ".env"
        
        if env_path.exists():
            load_dotenv(str(env_path))
            
            # Save to QSettings so they appear in UI
            env_vars = {
                "openai_key": os.getenv("OPENAI_API_KEY", ""),
                "hubspot_key": os.getenv("HUBSPOT_API_KEY", ""),
                "clearbit_key": os.getenv("CLEARBIT_API_KEY", ""),
                "data_source_type": os.getenv("DATA_SOURCE_TYPE", "csv"),
                "csv_file_path": os.getenv("CSV_FILE_PATH", "ai_agents/data/company_names.csv"),
                "sheet_url": os.getenv("GOOGLE_SHEET_URL", ""),
                "worksheet_name": os.getenv("GOOGLE_WORKSHEET_NAME", "Sheet1"),
                "max_companies": int(os.getenv("MAX_COMPANIES", "100")),
                "browser_timeout": int(os.getenv("BROWSER_TIMEOUT", "30")),
                "create_hubspot_contacts": os.getenv("CREATE_HUBSPOT_CONTACTS", "true").lower() == "true",
                "hubspot_owner_email": os.getenv("HUBSPOT_OWNER_EMAIL", ""),
            }
            
            for key, value in env_vars.items():
                if value:  # Only save non-empty values
                    self.settings.setValue(key, value)

    def load_from_env(self):
        """Load configuration from .env file"""
        load_dotenv()

        self.openai_key.setText(os.getenv("OPENAI_API_KEY", ""))
        self.hubspot_key.setText(os.getenv("HUBSPOT_API_KEY", ""))
        self.clearbit_key.setText(os.getenv("CLEARBIT_API_KEY", ""))
        self.data_source_type.setCurrentText(os.getenv("DATA_SOURCE_TYPE", "csv"))
        self.csv_file_path.setText(os.getenv("CSV_FILE_PATH", "ai_agents/data/company_names.csv"))
        self.sheet_url.setText(os.getenv("GOOGLE_SHEET_URL", ""))
        self.worksheet_name.setText(os.getenv("GOOGLE_WORKSHEET_NAME", ""))
        self.max_companies.setValue(int(os.getenv("MAX_COMPANIES", "100")))
        self.browser_timeout.setValue(int(os.getenv("BROWSER_TIMEOUT", "30")))
        self.create_hubspot_contacts.setChecked(os.getenv("CREATE_HUBSPOT_CONTACTS", "true").lower() == "true")
        self.hubspot_owner_email.setText(os.getenv("HUBSPOT_OWNER_EMAIL", ""))

        self.on_data_source_changed()
        QMessageBox.information(self, "Success", "Configuration loaded from .env file!")

    def test_configuration(self):
        """Test the current configuration"""
        try:
            config = self.get_configuration()

            # Test OpenAI API key
            if not config.get("openai_api_key"):
                raise ValueError("OpenAI API key is required")

            # Test data source
            data_source = config.get("data_source", {})
            if data_source.get("type") == "csv":
                csv_path = data_source.get("file_path")
                if csv_path and not os.path.exists(csv_path):
                    raise ValueError(f"CSV file not found: {csv_path}")
            elif data_source.get("type") == "google_sheets":
                if not data_source.get("sheet_url"):
                    raise ValueError("Google Sheets URL is required")

            QMessageBox.information(self, "Success", "Configuration is valid!")

        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", str(e))

    def reset_to_defaults(self):
        """Reset all configuration fields to default values"""
        reply = QMessageBox.question(
            self, "Reset Configuration",
            "This will clear all configuration fields and reset them to default values.\n\n"
            "Any unsaved changes will be lost. Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear all form fields
            self.openai_key.clear()
            self.hubspot_key.clear()
            self.clearbit_key.clear()
            
            # Reset to defaults
            self.data_source_type.setCurrentText("csv")
            self.csv_file_path.setText("ai_agents/data/company_names.csv")
            self.sheet_url.clear()
            self.worksheet_name.setText("Sheet1")
            self.max_companies.setValue(100)
            self.browser_timeout.setValue(30)
            self.create_hubspot_contacts.setChecked(True)
            self.hubspot_owner_email.clear()
            
            # Clear QSettings
            self.settings.clear()
            
            # Update UI
            self.on_data_source_changed()
            
            QMessageBox.information(
                self, "Reset Complete",
                "Configuration has been reset to default values.\n\n"
                "Remember to add your API keys before running the workflow."
            )

    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        return {
            "openai_api_key": self.openai_key.text(),
            "data_source": {
                "type": self.data_source_type.currentText(),
                "file_path": self.csv_file_path.text() or "ai_agents/data/company_names.csv",
                "sheet_url": self.sheet_url.text(),
                "worksheet_name": self.worksheet_name.text()
            },
            "clearbit_api_key": self.clearbit_key.text(),
            "browser_timeout": self.browser_timeout.value(),
            "max_companies": self.max_companies.value(),
            "hubspot_api_key": self.hubspot_key.text(),
            "hubspot_owner_email": self.hubspot_owner_email.text(),
            "create_hubspot_contacts": self.create_hubspot_contacts.isChecked(),
            "custom_prompts": {},  # Will be populated by prompts tab
        }


class WorkflowThread(QThread):
    """Background thread to run the SDR workflow"""

    progress_update = pyqtSignal(str)
    status_update = pyqtSignal(str)
    completion_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    log_message = pyqtSignal(str)
    cancellation_signal = pyqtSignal()  # New signal for cancellation

    def __init__(self, config):
        super(WorkflowThread, self).__init__()
        self.config = config
        self.is_running = False
        self.should_stop = False  # Cancellation flag
        self.current_task = None  # Store the asyncio task

    def run(self):
        """Run the workflow in background thread"""
        self.is_running = True
        self.should_stop = False
        gui_log_handler = None

        try:
            self.status_update.emit("Starting SDR workflow...")

            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Clear any existing GUI callbacks and register ours
                clear_all_gui_callbacks()

                def gui_log_handler(message):
                    """Handle log messages for GUI"""
                    self.progress_update.emit(message)

                register_gui_callback(gui_log_handler)

                self.progress_update.emit("Workflow compiled, starting execution...")

                # Create the workflow task
                self.current_task = loop.create_task(self._run_workflow_with_cancellation())

                # Run until completion or cancellation
                final_state = loop.run_until_complete(self.current_task)

                if not self.should_stop:
                    # Set completion time
                    final_state["completed_at"] = datetime.now()

                    # Convert to dictionary for signal
                    result_dict = {
                        "success": True,
                        "companies_processed": len(final_state["companies"]),
                        "linkedin_profiles": len(final_state.get('all_linkedin_profiles', [])),
                        "errors": final_state["errors"],
                        "run_directories": final_state.get("run_directories", {}),
                        "run_id": final_state["run_id"]
                    }

                    self.completion_signal.emit(result_dict)
                else:
                    # Workflow was cancelled
                    self.progress_update.emit("Workflow cancelled by user")
                    self.cancellation_signal.emit()

            except asyncio.CancelledError:
                self.progress_update.emit("Workflow cancelled by user")
                self.cancellation_signal.emit()
            except Exception as e:
                if not self.should_stop:
                    error_msg = f"Workflow execution failed: {str(e)}\n{traceback.format_exc()}"
                    self.error_signal.emit(error_msg)

            finally:
                # Cleanup GUI callback
                if gui_log_handler:
                    unregister_gui_callback(gui_log_handler)
                loop.close()

        except Exception as e:
            # Cleanup GUI callback on error too
            if gui_log_handler:
                try:
                    unregister_gui_callback(gui_log_handler)
                except:
                    pass
            if not self.should_stop:
                error_msg = f"Workflow failed: {str(e)}\n{traceback.format_exc()}"
                self.error_signal.emit(error_msg)
        finally:
            self.is_running = False
            self.current_task = None

    async def _run_workflow_with_cancellation(self):
        """Run workflow with periodic cancellation checks"""

        # Create a task for the main workflow
        workflow_task = asyncio.create_task(wf_main())

        # Create a task that checks for cancellation
        async def cancellation_checker():
            while not self.should_stop:
                await asyncio.sleep(0.1)  # Check every 100ms
            workflow_task.cancel()

        checker_task = asyncio.create_task(cancellation_checker())

        try:
            # Wait for either workflow completion or cancellation
            done, pending = await asyncio.wait(
                [workflow_task, checker_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel any remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Return the workflow result if it completed
            if workflow_task in done and not workflow_task.cancelled():
                return workflow_task.result()
            else:
                raise asyncio.CancelledError("Workflow was cancelled")

        except asyncio.CancelledError:
            # Ensure both tasks are cancelled
            workflow_task.cancel()
            checker_task.cancel()
            raise

    def stop(self):
        """Stop the workflow gracefully"""
        self.should_stop = True
        self.progress_update.emit("Stopping workflow...")

        # Give it a moment to stop gracefully
        if self.current_task and not self.current_task.done():
            # The cancellation checker will handle the actual cancellation
            pass

        # If it doesn't stop within a reasonable time, we could force terminate
        # but let's try graceful first


class PromptsTab(QWidget):
    """Custom prompts configuration tab"""

    def __init__(self):
        super(PromptsTab, self).__init__()
        self.custom_prompts = {}
        self.init_ui()
        self.load_prompts_at_startup()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("Custom Prompts Configuration")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        # Description
        desc = QLabel("Customize the AI prompts used in the workflow. Leave blank to use defaults.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Buttons
        button_layout = QHBoxLayout()
        load_defaults_btn = QPushButton("Load Defaults")
        load_defaults_btn.clicked.connect(self.load_default_prompts)
        load_defaults_btn.setProperty("class", "secondary")
        load_btn = QPushButton("Load from File")
        load_btn.clicked.connect(self.load_prompts_file)
        load_btn.setProperty("class", "secondary")
        save_btn = QPushButton("Save to File")
        save_btn.clicked.connect(self.save_prompts_file)
        save_btn.setProperty("class", "secondary")
        reset_btn = QPushButton("Clear All")
        reset_btn.clicked.connect(self.reset_prompts)
        reset_btn.setProperty("class", "danger")
        reset_btn.setToolTip("Clear all custom prompts (will use system defaults)")

        button_layout.addWidget(load_defaults_btn)
        button_layout.addWidget(load_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Scrollable prompts area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.prompts_layout = QVBoxLayout()

        # Add prompt editors for all available prompts
        self.add_prompt_editor("LinkedIn Research Instructions", "prospect_enricher_instructions",
                               "System instructions for LinkedIn research agent with browser access")
        self.add_prompt_editor("LinkedIn User Prompt", "prospect_enricher_user_prompt",
                               "User prompt template for LinkedIn prospect search")
        self.add_prompt_editor("LinkedIn Retry Prompt", "prospect_enricher_retry_prompt",
                               "Retry prompt template for failed LinkedIn searches")
        self.add_prompt_editor("Web Research System Prompt", "web_enricher_system_prompt",
                               "System prompt for comprehensive web research and analysis")
        self.add_prompt_editor("Web Research User Prompt", "web_enricher_user_prompt",
                               "User prompt for web research relevance criteria")
        self.add_prompt_editor("Web Research Output Format", "web_enricher_output_format",
                               "JSON output format specification for web research")
        self.add_prompt_editor("HubSpot Creator Instructions", "hubspot_creator_instructions",
                               "System instructions for HubSpot contact creation")
        self.add_prompt_editor("HubSpot Creator User Prompt", "hubspot_creator_user_prompt",
                               "User prompt template for HubSpot contact processing")
        self.add_prompt_editor("HubSpot Creator Retry Prompt", "hubspot_creator_retry_prompt",
                               "Retry prompt template for failed HubSpot operations")
        self.add_prompt_editor("Target Executives List", "prospect_enricher_target_executives",
                               "Define target executive roles to search for on LinkedIn")

        scroll_widget.setLayout(self.prompts_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def load_prompts_at_startup(self):
        """Load prompts at startup - either custom or defaults"""
        # Always try to load prompts from file first, then fallback to defaults
        current_dir = Path(__file__).parent
        config_dir = current_dir / "sdr" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)  # Ensure config directory exists
        custom_prompts_file = config_dir / "custom_prompts.json"
        
        if custom_prompts_file.exists():
            try:
                # Load from existing custom prompts file
                prompts = load_prompts_from_file(str(custom_prompts_file))
                self.set_prompts(prompts)
                print(f"Loaded custom prompts from {custom_prompts_file}")
            except Exception as e:
                # If loading fails, fall back to defaults
                print(f"Failed to load custom prompts: {e}")
                self.set_prompts(DEFAULT_PROMPTS)
        else:
            # No custom file exists, load defaults
            self.set_prompts(DEFAULT_PROMPTS)
            print("Loaded default prompts")

    def add_prompt_editor(self, title: str, key: str, description: str):
        """Add a prompt editor section"""
        group = QGroupBox(title)
        group_layout = QVBoxLayout()

        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        group_layout.addWidget(desc_label)

        # Text editor
        editor = QTextEdit()
        editor.setMaximumHeight(150)
        editor.setPlaceholderText(f"Leave blank to use default {title.lower()}...")
        group_layout.addWidget(editor)

        group.setLayout(group_layout)
        self.prompts_layout.addWidget(group)

        # Store reference
        setattr(self, f"{key}_editor", editor)

    def load_prompts_file(self):
        """Load prompts from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Prompts", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                prompts = load_prompts_from_file(file_path)
                self.set_prompts(prompts)
                QMessageBox.information(self, "Success", "Prompts loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load prompts: {str(e)}")

    def save_prompts_file(self):
        """Save prompts to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Prompts", "custom_prompts.json", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                prompts = self.get_prompts()
                save_prompts_to_file(prompts, file_path)
                QMessageBox.information(self, "Success", "Prompts saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save prompts: {str(e)}")

    def load_default_prompts(self):
        """Load default prompts from the prompts module"""
        reply = QMessageBox.question(
            self, "Load Default Prompts",
            "Load all default prompts? This will overwrite any current custom prompts.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.set_prompts(DEFAULT_PROMPTS)
            QMessageBox.information(self, "Success", "Default prompts loaded successfully!")

    def reset_prompts(self):
        """Clear all prompts (use system defaults)"""
        reply = QMessageBox.question(
            self, "Clear All Prompts",
            "Are you sure you want to clear all prompts? This will use system defaults.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.set_prompts({})

    def get_prompts(self) -> Dict[str, str]:
        """Get current custom prompts"""
        prompts = {}

        # Define the expected editor attributes
        editor_keys = [
            'prospect_enricher_instructions',
            'prospect_enricher_user_prompt',
            'prospect_enricher_retry_prompt',
            'web_enricher_system_prompt',
            'web_enricher_user_prompt',
            'web_enricher_output_format',
            'hubspot_creator_instructions',
            'hubspot_creator_user_prompt',
            'hubspot_creator_retry_prompt',
            'prospect_enricher_target_executives'
        ]

        # Get text from all editors
        for key in editor_keys:
            editor_attr = f"{key}_editor"
            if hasattr(self, editor_attr):
                editor = getattr(self, editor_attr)
                if hasattr(editor, 'toPlainText'):  # Ensure it's a QTextEdit
                    text = editor.toPlainText().strip()
                    if text:  # Only include non-empty prompts
                        prompts[key] = text

        return prompts

    def set_prompts(self, prompts: Dict[str, str]):
        """Set prompts in editors"""
        for key, value in prompts.items():
            editor_attr = f"{key}_editor"
            if hasattr(self, editor_attr):
                editor = getattr(self, editor_attr)
                editor.setPlainText(value)


class ExecutionTab(QWidget):
    """Workflow execution and monitoring tab"""

    def __init__(self, main_window):
        super(ExecutionTab, self).__init__()
        self.progress_log = None
        self.main_window = main_window
        self.workflow_thread = None
        self.current_log_file = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Control buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶️ Start Workflow")
        self.start_btn.clicked.connect(self.start_workflow)
        self.start_btn.setProperty("class", "success")

        self.stop_btn = QPushButton("⏹️ Stop Workflow")
        self.stop_btn.clicked.connect(self.stop_workflow)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setProperty("class", "danger")

        self.view_logs_btn = QPushButton("📝 View Logs")
        self.view_logs_btn.clicked.connect(self.view_logs)
        self.view_logs_btn.setProperty("class", "secondary")
        self.view_logs_btn.setEnabled(False)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.view_logs_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Status section
        status_group = QGroupBox("📊 Workflow Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Ready to start")
        self.status_label.setProperty("class", "status-ready")
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Progress log
        log_group = QGroupBox("📝 Progress Log")
        log_layout = QVBoxLayout()

        self.progress_log = QTextEdit()
        self.progress_log.setReadOnly(True)
        self.progress_log.setMaximumHeight(200)
        log_layout.addWidget(self.progress_log)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Results summary
        results_group = QGroupBox("📈 Results Summary")
        results_layout = QGridLayout()

        self.companies_label = QLabel("Companies: 0")
        self.profiles_label = QLabel("LinkedIn Profiles: 0")
        self.contacts_label = QLabel("HubSpot Contacts: 0")
        self.errors_label = QLabel("Errors: 0")

        results_layout.addWidget(self.companies_label, 0, 0)
        results_layout.addWidget(self.profiles_label, 0, 1)
        results_layout.addWidget(self.contacts_label, 1, 0)
        results_layout.addWidget(self.errors_label, 1, 1)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        layout.addStretch()
        self.setLayout(layout)

    def start_workflow(self):
        """Start the SDR workflow"""
        try:
            # Get configuration from main window
            config_tab = self.main_window.config_tab
            prompts_tab = self.main_window.prompts_tab

            # Validate configuration
            config = config_tab.get_configuration()
            if not config.get("openai_api_key"):
                QMessageBox.critical(self, "Configuration Error", "OpenAI API key is required!")
                return

            # Add custom prompts
            config["custom_prompts"] = prompts_tab.get_prompts()

            # Create run directories
            run_directories = create_run_directories()
            config["run_directories"] = run_directories

            # Update UI
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_label.setText("Starting workflow...")
            self.progress_log.clear()

            # Start workflow thread
            self.workflow_thread = WorkflowThread(config)
            self.workflow_thread.progress_update.connect(self.update_progress)
            self.workflow_thread.status_update.connect(self.update_status)
            self.workflow_thread.completion_signal.connect(self.workflow_completed)
            self.workflow_thread.error_signal.connect(self.workflow_error)
            self.workflow_thread.cancellation_signal.connect(self.workflow_cancelled)  # New connection

            # Connect real-time log updates
            if hasattr(self.workflow_thread, 'log_message'):
                self.workflow_thread.log_message.connect(self.update_progress)

            # Store log file path for view logs button using centralized logging
            self.current_log_file = get_log_file_path("workflow")
            self.view_logs_btn.setEnabled(True)

            self.workflow_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start workflow: {str(e)}")
            self.reset_ui()

    def stop_workflow(self):
        """Stop the running workflow"""
        if self.workflow_thread and self.workflow_thread.is_running:
            reply = QMessageBox.question(
                self, "Stop Workflow",
                "Are you sure you want to stop the running workflow?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.progress_log.append("Stopping workflow...")
                self.workflow_thread.stop()
                # Don't reset UI immediately - wait for cancellation signal

    @pyqtSlot(str)
    def update_progress(self, message):
        """Update progress log"""
        # timestamp = datetime.now().strftime("%H:%M:%S")
        # self.progress_log.append(f"[{timestamp}] {message}")
        self.progress_log.append(f"{message}")
        self.progress_log.moveCursor(QTextCursor.MoveOperation.End)

    @pyqtSlot(str)
    def update_status(self, status):
        """Update status label"""
        self.status_label.setText(status)

    @pyqtSlot(dict)
    def workflow_completed(self, results):
        """Handle workflow completion"""
        self.reset_ui()

        # Update results summary
        self.companies_label.setText(f"Companies: {results.get('companies_processed', 0)}")
        self.profiles_label.setText(f"LinkedIn Profiles: {results.get('linkedin_profiles', 0)}")
        self.errors_label.setText(f"Errors: {len(results.get('errors', []))}")

        self.status_label.setText("Workflow completed successfully!")
        self.status_label.setProperty("class", "status-success")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        # Show completion message
        QMessageBox.information(
            self, "Workflow Complete",
            f"SDR Workflow completed successfully!\n\n"
            f"Companies processed: {results.get('companies_processed', 0)}\n"
            f"LinkedIn profiles found: {results.get('linkedin_profiles', 0)}\n"
            f"Run ID: {results.get('run_id', 'Unknown')}"
        )

        # Update results tab
        if hasattr(self.main_window, 'results_tab'):
            self.main_window.results_tab.load_results(results)

    @pyqtSlot(str)
    def workflow_error(self, error_message):
        """Handle workflow error"""
        self.reset_ui()
        self.status_label.setText("Workflow failed")
        self.status_label.setProperty("class", "status-error")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        QMessageBox.critical(self, "Workflow Error", f"Workflow failed:\n\n{error_message}")

    @pyqtSlot()
    def workflow_cancelled(self):
        """Handle workflow cancellation"""
        self.reset_ui()
        self.status_label.setText("Workflow cancelled by user")
        self.status_label.setProperty("class", "status-warning")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        self.progress_log.append("Workflow cancelled successfully")

        QMessageBox.information(
            self, "Workflow Cancelled",
            "The workflow has been cancelled successfully."
        )

    def view_logs(self):
        """Open log viewer dialog or switch to logs view"""
        if self.current_log_file and os.path.exists(self.current_log_file):
            try:
                # Create a simple log viewer dialog
                dialog = QDialog(self)
                dialog.setWindowTitle("Workflow Logs")
                dialog.setModal(False)
                dialog.resize(800, 600)

                layout = QVBoxLayout()

                # Header with file info
                header_layout = QHBoxLayout()
                file_label = QLabel(f"Log File: {os.path.basename(self.current_log_file)}")
                file_label.setStyleSheet("font-weight: 600; color: #374151;")

                refresh_btn = QPushButton("Refresh")
                refresh_btn.setProperty("class", "secondary")

                header_layout.addWidget(file_label)
                header_layout.addStretch()
                header_layout.addWidget(refresh_btn)
                layout.addLayout(header_layout)

                # Log content viewer
                log_viewer = QTextEdit()
                log_viewer.setReadOnly(True)

                # Set monospace font
                monospace_font = QFont()
                if sys.platform == "darwin":  # macOS
                    monospace_font.setFamily("SF Mono")
                elif sys.platform == "win32":  # Windows
                    monospace_font.setFamily("Courier New")
                else:  # Linux
                    monospace_font.setFamily("DejaVu Sans Mono")
                monospace_font.setStyleHint(QFont.StyleHint.TypeWriter)
                monospace_font.setPointSize(10)
                log_viewer.setFont(monospace_font)

                # Load initial content
                def refresh_content():
                    try:
                        with open(self.current_log_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            log_viewer.setPlainText(content)
                            # Auto-scroll to bottom
                            log_viewer.moveCursor(QTextCursor.MoveOperation.End)
                    except Exception as e:
                        log_viewer.setPlainText(f"Error reading log file: {str(e)}")

                refresh_content()
                refresh_btn.clicked.connect(refresh_content)

                layout.addWidget(log_viewer)

                # Buttons
                button_layout = QHBoxLayout()
                auto_refresh_cb = QCheckBox("Auto-refresh every 2 seconds")

                # Auto-refresh timer
                timer = QTimer()
                timer.timeout.connect(refresh_content)

                def toggle_auto_refresh(checked):
                    if checked:
                        timer.start(2000)  # 2 seconds
                    else:
                        timer.stop()

                auto_refresh_cb.toggled.connect(toggle_auto_refresh)

                close_btn = QPushButton("Close")
                close_btn.clicked.connect(dialog.close)

                button_layout.addWidget(auto_refresh_cb)
                button_layout.addStretch()
                button_layout.addWidget(close_btn)
                layout.addLayout(button_layout)

                dialog.setLayout(layout)
                dialog.show()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open log viewer: {str(e)}")
        else:
            QMessageBox.warning(self, "No Logs", "No log file available yet. Start a workflow first.")

    def reset_ui(self):
        """Reset UI to initial state"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)


class ResultsTab(QWidget):
    """Results viewing and analysis tab"""

    def __init__(self):
        super(ResultsTab, self).__init__()
        self.current_results = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header with refresh button
        header_layout = QHBoxLayout()
        header = QLabel("Workflow Results")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        self.refresh_btn = QPushButton("Refresh Results")
        self.refresh_btn.clicked.connect(self.refresh_results)
        self.refresh_btn.setProperty("class", "secondary")

        self.open_folder_btn = QPushButton("Open Results Folder")
        self.open_folder_btn.clicked.connect(self.open_results_folder)
        self.open_folder_btn.setProperty("class", "secondary")

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.open_folder_btn)
        layout.addLayout(header_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        layout.addWidget(self.results_table)

        # Details section
        details_group = QGroupBox("Run Details")
        details_layout = QFormLayout()

        self.run_id_label = QLabel("-")
        self.companies_count_label = QLabel("-")
        self.profiles_count_label = QLabel("-")
        self.errors_count_label = QLabel("-")
        self.duration_label = QLabel("-")

        details_layout.addRow("Run ID:", self.run_id_label)
        details_layout.addRow("Companies Processed:", self.companies_count_label)
        details_layout.addRow("LinkedIn Profiles:", self.profiles_count_label)
        details_layout.addRow("Errors:", self.errors_count_label)
        details_layout.addRow("Duration:", self.duration_label)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        self.setLayout(layout)

    def load_results(self, results: Dict[str, Any]):
        """Load and display workflow results"""
        self.current_results = results

        # Update details
        self.run_id_label.setText(str(results.get('run_id', '-')))
        self.companies_count_label.setText(str(results.get('companies_processed', 0)))
        self.profiles_count_label.setText(str(results.get('linkedin_profiles', 0)))
        self.errors_count_label.setText(str(len(results.get('errors', []))))

        # Update table (placeholder - would need actual results data structure)
        self.update_results_table()

    def update_results_table(self):
        """Update the results table"""
        if not self.current_results:
            return

        # This is a placeholder - you would implement based on your actual results structure
        self.results_table.setRowCount(1)
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Company", "Profiles Found", "HubSpot Status", "Errors"])

        # Sample data
        self.results_table.setItem(0, 0, QTableWidgetItem("Sample Company"))
        self.results_table.setItem(0, 1, QTableWidgetItem("5"))
        self.results_table.setItem(0, 2, QTableWidgetItem("Created"))
        self.results_table.setItem(0, 3, QTableWidgetItem("None"))

    def refresh_results(self):
        """Refresh results from latest run"""
        # Implement loading from latest run directory
        QMessageBox.information(self, "Info", "Results refreshed (placeholder)")

    def open_results_folder(self):
        """Open results folder in file explorer"""
        if self.current_results and 'run_directories' in self.current_results:
            folder_path = self.current_results['run_directories'].get('final_dir')
            if folder_path and os.path.exists(folder_path):
                if sys.platform == "darwin":  # macOS
                    subprocess.run(["open", folder_path])
                elif sys.platform == "win32":  # Windows
                    subprocess.run(["explorer", folder_path])
                else:  # Linux
                    subprocess.run(["xdg-open", folder_path])
            else:
                QMessageBox.warning(self, "Warning", "Results folder not found")
        else:
            QMessageBox.warning(self, "Warning", "No results available")


class LogViewerTab(QWidget):
    """Log viewer tab for monitoring workflow logs"""

    def __init__(self):
        super(LogViewerTab, self).__init__()
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_logs)
        self.current_log_file = None

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Workflow Logs")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        self.auto_refresh_cb = QCheckBox("Auto-refresh")
        self.auto_refresh_cb.toggled.connect(self.toggle_auto_refresh)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.manual_refresh)
        refresh_btn.setProperty("class", "secondary")

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_logs)
        clear_btn.setProperty("class", "secondary")

        open_folder_btn = QPushButton("Open Logs Folder")
        open_folder_btn.clicked.connect(self.open_logs_folder)
        open_folder_btn.setProperty("class", "secondary")

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.auto_refresh_cb)
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(clear_btn)
        header_layout.addWidget(open_folder_btn)
        layout.addLayout(header_layout)

        # Log file info
        self.log_info_label = QLabel("No log file selected")
        self.log_info_label.setStyleSheet("color: #666; font-size: 11px; padding: 4px;")
        layout.addWidget(self.log_info_label)

        # Log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        # Use system monospace font instead of Consolas
        monospace_font = QFont()
        # Try different monospace fonts based on platform
        if sys.platform == "darwin":  # macOS
            monospace_font.setFamily("SF Mono")
        elif sys.platform == "win32":  # Windows
            monospace_font.setFamily("Courier New")
        else:  # Linux
            monospace_font.setFamily("DejaVu Sans Mono")

        # Fallback to system monospace if specific font not available
        monospace_font.setStyleHint(QFont.StyleHint.TypeWriter)
        monospace_font.setPointSize(10)
        self.log_viewer.setFont(monospace_font)
        self.log_viewer.setPlaceholderText(
            "Workflow logs will appear here when a workflow is running...\n\nTip: The 'Progress Log' in the Execution "
            "tab shows real-time updates,\nwhile this tab shows detailed file-based logs saved to disk.")
        layout.addWidget(self.log_viewer)

        self.setLayout(layout)

    def toggle_auto_refresh(self, enabled):
        """Toggle auto-refresh of logs"""
        if enabled:
            self.timer.start(500)  # Refresh every 0.5 seconds for more real-time feel
        else:
            self.timer.stop()

    def manual_refresh(self):
        """Manually refresh logs"""
        self.refresh_logs()

    def refresh_logs(self):
        """Refresh log content"""
        if self.current_log_file:
            if os.path.exists(self.current_log_file):
                try:
                    # Get current scroll position
                    scrollbar = self.log_viewer.verticalScrollBar()
                    was_at_bottom = scrollbar.value() == scrollbar.maximum()

                    with open(self.current_log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Only update if content has changed
                        if self.log_viewer.toPlainText() != content:
                            self.log_viewer.setPlainText(content)
                            # Only scroll to bottom if we were already at bottom
                            if was_at_bottom:
                                self.log_viewer.moveCursor(QTextCursor.MoveOperation.End)
                except Exception as e:
                    self.log_viewer.setPlainText(f"Error reading log file: {str(e)}")
            else:
                self.log_viewer.setPlainText(
                    f"Log file not yet created: {self.current_log_file}\n\nThe log file will be created when the "
                    f"workflow starts processing.")
        else:
            self.log_viewer.clear()

    def clear_logs(self):
        """Clear log viewer"""
        self.log_viewer.clear()

    def set_log_file(self, log_file_path):
        """Set the current log file to monitor"""
        self.current_log_file = log_file_path
        if log_file_path:
            self.log_info_label.setText(f"Monitoring: {os.path.basename(log_file_path)}")
            self.log_info_label.setToolTip(log_file_path)
        else:
            self.log_info_label.setText("No log file selected")
            self.log_info_label.setToolTip("")
        self.refresh_logs()

    def open_logs_folder(self):
        """Open the logs folder in file explorer"""
        if self.current_log_file:
            folder_path = os.path.dirname(self.current_log_file)
            if os.path.exists(folder_path):
                if sys.platform == "darwin":  # macOS
                    subprocess.run(["open", folder_path])
                elif sys.platform == "win32":  # Windows
                    subprocess.run(["explorer", folder_path])
                else:  # Linux
                    subprocess.run(["xdg-open", folder_path])
            else:
                QMessageBox.warning(self, "Warning", "Logs folder not found")
        else:
            QMessageBox.warning(self, "Warning", "No log file selected")


class ResponsiveSDRMainWindow(QMainWindow):
    """Main application window with responsive design"""

    def __init__(self):
        super(ResponsiveSDRMainWindow, self).__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SDR Workflow - Responsive GUI")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(600, 500)  # Allow smaller window size

        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)  # Smaller margins for small windows

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.config_tab = ResponsiveConfigurationTab()
        self.prompts_tab = PromptsTab()
        self.execution_tab = ExecutionTab(self)
        self.results_tab = ResultsTab()

        # Add tabs
        self.tab_widget.addTab(self.config_tab, "Configuration")
        self.tab_widget.addTab(self.prompts_tab, "Custom Prompts")
        self.tab_widget.addTab(self.execution_tab, "Execution")
        self.tab_widget.addTab(self.results_tab, "Results")

        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.statusBar().showMessage("Ready")

        # Apply styles
        self.apply_styles()

        # Use QTimer to show setup wizard after window is fully shown
        QTimer.singleShot(100, self.show_setup_wizard_if_needed)

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        # Load config action
        load_config_action = QAction('Load Configuration', self)
        load_config_action.triggered.connect(self.config_tab.load_from_env)
        file_menu.addAction(load_config_action)

        # Save config action
        save_config_action = QAction('Save Configuration', self)
        save_config_action.triggered.connect(self.config_tab.save_settings)
        file_menu.addAction(save_config_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        # Setup wizard action
        setup_action = QAction('Show Setup Wizard', self)
        setup_action.triggered.connect(self.force_show_setup_wizard)
        help_menu.addAction(setup_action)

        # Reset first run action
        reset_action = QAction('Reset First Run Status', self)
        reset_action.triggered.connect(self.reset_first_run_status)
        help_menu.addAction(reset_action)

        help_menu.addSeparator()

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About SDR Workflow",
            "SDR Workflow - Responsive GUI\n\n"
            "A comprehensive workflow for Sales Development Representatives\n"
            "featuring LinkedIn prospect enrichment and HubSpot integration.\n\n"
            "Built with PyQt6 and Python."
        )

    def apply_styles(self):
        """Apply custom styles to the application"""
        style = """
        /* Main window and base styling */
        QMainWindow {
            background-color: #f8fafc;
            color: #1e293b;
        }
        
        /* Tab widget styling */
        QTabWidget::pane {
            border: none;
            background-color: #ffffff;
            border-radius: 8px;
            margin-top: 4px;
        }
        
        QTabBar::tab {
            background-color: transparent;
            color: #64748b;
            padding: 8px 16px;
            margin-right: 2px;
            border-radius: 6px 6px 0 0;
            font-weight: 500;
            font-size: 13px;
            min-width: 80px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            color: #0f172a;
            border-bottom: 3px solid #3b82f6;
            font-weight: 600;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #f1f5f9;
            color: #475569;
        }
        
        /* Group box styling */
        QGroupBox {
            font-weight: 600;
            font-size: 13px;
            color: #374151;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: #ffffff;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            background-color: #ffffff;
            color: #1f2937;
        }
        
        /* Button styling */
        QPushButton {
            background-color: #3b82f6;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 13px;
            min-height: 16px;
        }
        
        QPushButton:hover {
            background-color: #2563eb;
        }
        
        QPushButton:pressed {
            background-color: #1d4ed8;
        }
        
        QPushButton:disabled {
            background-color: #9ca3af;
            color: #d1d5db;
        }
        
        /* Secondary button styling */
        QPushButton[class="secondary"] {
            background-color: #f8fafc;
            color: #475569;
            border: 2px solid #e2e8f0;
            font-weight: 500;
        }
        
        QPushButton[class="secondary"]:hover {
            background-color: #f1f5f9;
            border-color: #cbd5e1;
            color: #374151;
        }
        
        /* Success button styling */
        QPushButton[class="success"] {
            background-color: #10b981;
            color: white;
        }
        
        QPushButton[class="success"]:hover {
            background-color: #059669;
        }
        
        /* Danger button styling */
        QPushButton[class="danger"] {
            background-color: #ef4444;
            color: white;
        }
        
        QPushButton[class="danger"]:hover {
            background-color: #dc2626;
        }
        
        /* Input field styling */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            color: #374151;
            selection-background-color: #dbeafe;
            min-height: 16px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #3b82f6;
            outline: none;
        }
        
        QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {
            color: #9ca3af;
        }
        
        /* ComboBox styling */
        QComboBox {
            background-color: #ffffff;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            color: #374151;
            min-height: 16px;
        }
        
        QComboBox:focus {
            border-color: #3b82f6;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #6b7280;
            margin-right: 4px;
        }
        
        /* SpinBox styling */
        QSpinBox {
            background-color: #ffffff;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            color: #374151;
            min-height: 16px;
        }
        
        QSpinBox:focus {
            border-color: #3b82f6;
        }
        
        /* CheckBox styling */
        QCheckBox {
            color: #374151;
            font-size: 13px;
            spacing: 8px;
            font-weight: 500;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #d1d5db;
            border-radius: 4px;
            background-color: #ffffff;
        }
        
        QCheckBox::indicator:checked {
            background-color: #3b82f6;
            border-color: #3b82f6;
        }
        
        /* Label styling */
        QLabel {
            color: #374151;
            font-size: 13px;
        }
        
        /* Progress bar styling */
        QProgressBar {
            background-color: #f3f4f6;
            border: none;
            border-radius: 6px;
            text-align: center;
            font-weight: 500;
            height: 6px;
        }
        
        QProgressBar::chunk {
            background-color: #3b82f6;
            border-radius: 6px;
        }
        
        /* ScrollArea styling */
        QScrollArea {
            background-color: transparent;
            border: none;
        }
        
        /* Scrollbar styling */
        QScrollBar:vertical {
            background-color: #f3f4f6;
            width: 10px;
            border-radius: 5px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #d1d5db;
            border-radius: 5px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #9ca3af;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* Status labels */
        QLabel[class="status-ready"] {
            color: #059669;
            font-weight: 600;
        }
        
        QLabel[class="status-running"] {
            color: #d97706;
            font-weight: 600;
        }
        
        QLabel[class="status-error"] {
            color: #dc2626;
            font-weight: 600;
        }
        
        QLabel[class="status-success"] {
            color: #059669;
            font-weight: 600;
        }
        
        /* Table widget styling */
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f9fafb;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            gridline-color: #f3f4f6;
            font-size: 13px;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #f3f4f6;
        }
        
        QTableWidget::item:selected {
            background-color: #dbeafe;
            color: #1e40af;
        }
        
        QHeaderView::section {
            background-color: #f8fafc;
            color: #374151;
            font-weight: 600;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #e5e7eb;
        }
        
        /* Menu bar styling */
        QMenuBar {
            background-color: #ffffff;
            color: #374151;
            border-bottom: 1px solid #e5e7eb;
            padding: 4px;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background-color: #f3f4f6;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            padding: 6px;
        }
        
        QMenu::item {
            padding: 6px 12px;
            border-radius: 4px;
        }
        
        QMenu::item:selected {
            background-color: #f3f4f6;
        }
        
        /* Status bar styling */
        QStatusBar {
            background-color: #f8fafc;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            padding: 2px 6px;
        }
        """

        self.setStyleSheet(style)

    def show_setup_wizard_if_needed(self):
        """Show setup wizard on first run"""
        settings = QSettings('SDR_Workflow', 'MainWindow')
        first_run = settings.value("first_run", True, type=bool)

        if first_run:
            # Create simple setup dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Welcome to AI SDR Agent")
            dialog.setModal(True)
            dialog.setFixedSize(500, 350)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    color: #1f2937;
                }
                QLabel {
                    color: #1f2937;
                    background-color: transparent;
                }
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: 500;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton[class="success"] {
                    background-color: #10b981;
                }
                QPushButton[class="success"]:hover {
                    background-color: #059669;
                }
                QPushButton[class="secondary"] {
                    background-color: #f3f4f6;
                    color: #374151;
                    border: 2px solid #d1d5db;
                }
                QPushButton[class="secondary"]:hover {
                    background-color: #e5e7eb;
                    border-color: #9ca3af;
                }
            """)

            layout = QVBoxLayout()

            # Welcome message
            welcome_label = QLabel("🎉 Welcome to AI SDR Agent!")
            welcome_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(welcome_label)

            info_text = QLabel("""
This is your first time using the AI SDR Agent. We've set up some defaults for you:

✅ Created a default .env configuration file
✅ Populated default AI prompts
✅ Set reasonable processing limits

Next steps:
1. Add your OpenAI API key in the Configuration tab
2. (Optional) Add HubSpot and Clearbit API keys
3. Upload your companies CSV file
4. Run your first workflow!

You can always customize prompts and settings later.
            """)
            info_text.setWordWrap(True)
            info_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(info_text)

            # Buttons
            button_layout = QHBoxLayout()

            config_btn = QPushButton("🔧 Go to Configuration")
            config_btn.setProperty("class", "success")
            config_btn.setToolTip("Switch to Configuration tab to add your API keys and settings")
            config_btn.clicked.connect(lambda: self.switch_to_config_tab(dialog, settings))

            later_btn = QPushButton("👋 I'll Set This Up Later")
            later_btn.setProperty("class", "secondary") 
            later_btn.setToolTip("Close this welcome dialog and explore the interface first")
            later_btn.clicked.connect(lambda: self.close_setup_wizard(dialog, settings))

            button_layout.addWidget(config_btn)
            button_layout.addWidget(later_btn)
            layout.addLayout(button_layout)

            dialog.setLayout(layout)

            # Center the dialog on the main window
            dialog.move(
                self.x() + (self.width() - dialog.width()) // 2,
                self.y() + (self.height() - dialog.height()) // 2
            )

            # Ensure dialog is visible and on top
            dialog.raise_()
            dialog.activateWindow()

            # Show dialog
            dialog.exec()

    def switch_to_config_tab(self, dialog, settings):
        """Switch to configuration tab and close dialog"""
        # Mark first run as complete
        settings.setValue("first_run", False)
        dialog.close()
        self.tab_widget.setCurrentIndex(0)  # Configuration is first tab

        # Show helpful tooltip
        QMessageBox.information(
            self, "Getting Started",
            "Add your OpenAI API key to get started.\n\n"
            "You can find your API key at: https://platform.openai.com/api-keys"
        )
    
    def close_setup_wizard(self, dialog, settings):
        """Close the setup wizard and mark first run as complete"""
        # Mark first run as complete
        settings.setValue("first_run", False)
        dialog.close()

    def force_show_setup_wizard(self):
        """Force show the setup wizard (ignoring first run setting)"""
        # Temporarily show the wizard regardless of first run status
        settings = QSettings('SDR_Workflow', 'MainWindow')
        original_first_run = settings.value("first_run", False, type=bool)
        settings.setValue("first_run", True)

        self.show_setup_wizard_if_needed()

        # Restore original setting if it was False
        if not original_first_run:
            settings.setValue("first_run", False)

    def reset_first_run_status(self):
        """Reset first run status - useful for testing or re-showing the wizard"""
        reply = QMessageBox.question(
            self, "Reset First Run Status",
            "This will reset the first run status and show the setup wizard again on next restart.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear all settings
            settings_main = QSettings('SDR_Workflow', 'MainWindow')
            settings_main.setValue("first_run", True)
            
            settings_config = QSettings('SDR_Workflow', 'Configuration')
            settings_config.clear()
            
            settings_prompts = QSettings('SDR_Workflow', 'PromptsConfiguration')
            settings_prompts.setValue("first_run", True)
            
            QMessageBox.information(
                self, "Reset Complete",
                "First run status has been reset.\n\n"
                "The setup wizard will appear on next restart, and default prompts will be reloaded."
            )


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("SDR Workflow GUI - Responsive")
    app.setOrganizationName("SDR Tools")

    try:
        # Create and show main window
        window = ResponsiveSDRMainWindow()
        window.show()

        return app.exec()
    except Exception as e:
        print(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
