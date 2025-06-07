#!/usr/bin/env python3
"""
Advanced SDR Workflow GUI

A comprehensive Qt-based interface for the SDR workflow application with:
- Configuration management
- Real-time progress tracking  
- Results visualization
- Log viewing
- Custom prompts editor
"""

import sys
import os
import json
import subprocess
import threading
import asyncio
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QGridLayout, QFormLayout, QProgressBar, QTreeWidget, QTreeWidgetItem,
    QSplitter, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame, QDialog, QDialogButtonBox, QPlainTextEdit
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSettings, pyqtSlot
)
from PyQt6.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap, QTextCursor, QAction
)

# Import your SDR modules
from dotenv import load_dotenv, set_key
from sdr.main import create_run_directories, load_configuration, run_tms_workflow
from sdr.prompts import get_user_prompts, load_prompts_from_file, save_prompts_to_file
from sdr.logging_config import setup_sdr_logging


class WorkflowThread(QThread):
    """Background thread to run the SDR workflow"""
    
    progress_update = pyqtSignal(str)
    status_update = pyqtSignal(str)
    completion_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = False
        
    def run(self):
        """Run the workflow in background thread"""
        self.is_running = True
        try:
            self.status_update.emit("Starting SDR workflow...")
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                from sdr.main import run_tms_workflow
                from sdr.models import WorkflowState
                from datetime import datetime
                
                # Initialize state
                initial_state = WorkflowState(
                    companies=[],
                    enriched_data={},
                    errors=[],
                    run_id=self.config["run_directories"]["run_id"],
                    started_at=datetime.now(),
                    all_linkedin_profiles=[],
                    run_directories=self.config["run_directories"]
                )
                
                # Import and compile workflow
                from sdr.graph import compile_workflow
                workflow = compile_workflow()
                
                self.progress_update.emit("Workflow compiled, starting execution...")
                
                # Run workflow
                final_state = loop.run_until_complete(
                    workflow.ainvoke(
                        initial_state,
                        config={"configurable": self.config, "recursion_limit": 10000}
                    )
                )
                
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
                
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = f"Workflow failed: {str(e)}\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)
        finally:
            self.is_running = False
    
    def stop(self):
        """Stop the workflow (if possible)"""
        self.is_running = False
        self.terminate()


class ConfigurationTab(QWidget):
    """Configuration tab for API keys and settings"""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('SDR_Workflow', 'Configuration')
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # API Configuration
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout()
        
        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key.setPlaceholderText("sk-...")
        api_layout.addRow("OpenAI API Key*:", self.openai_key)
        
        self.hubspot_key = QLineEdit()
        self.hubspot_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.hubspot_key.setPlaceholderText("Optional")
        api_layout.addRow("HubSpot API Key:", self.hubspot_key)
        
        self.clearbit_key = QLineEdit()
        self.clearbit_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.clearbit_key.setPlaceholderText("Optional")
        api_layout.addRow("Clearbit API Key:", self.clearbit_key)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Data Source Configuration
        data_group = QGroupBox("Data Source Configuration")
        data_layout = QFormLayout()
        
        self.data_source_type = QComboBox()
        self.data_source_type.addItems(["csv", "google_sheets"])
        self.data_source_type.currentTextChanged.connect(self.on_data_source_changed)
        data_layout.addRow("Data Source Type:", self.data_source_type)
        
        # CSV Configuration
        self.csv_widget = QWidget()
        csv_layout = QHBoxLayout()
        self.csv_file_path = QLineEdit()
        self.csv_file_path.setPlaceholderText("companies.csv")
        csv_browse_btn = QPushButton("Browse")
        csv_browse_btn.clicked.connect(self.browse_csv_file)
        csv_layout.addWidget(self.csv_file_path)
        csv_layout.addWidget(csv_browse_btn)
        self.csv_widget.setLayout(csv_layout)
        data_layout.addRow("CSV File Path:", self.csv_widget)
        
        # Google Sheets Configuration
        self.sheets_widget = QWidget()
        sheets_layout = QVBoxLayout()
        self.sheet_url = QLineEdit()
        self.sheet_url.setPlaceholderText("https://docs.google.com/spreadsheets/d/...")
        self.worksheet_name = QLineEdit()
        self.worksheet_name.setPlaceholderText("Sheet1 (optional)")
        sheets_layout.addWidget(self.sheet_url)
        sheets_layout.addWidget(self.worksheet_name)
        self.sheets_widget.setLayout(sheets_layout)
        data_layout.addRow("Google Sheet URL:", self.sheet_url)
        data_layout.addRow("Worksheet Name:", self.worksheet_name)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Processing Configuration
        process_group = QGroupBox("Processing Configuration")
        process_layout = QFormLayout()
        
        self.max_companies = QSpinBox()
        self.max_companies.setRange(1, 1000)
        self.max_companies.setValue(100)
        process_layout.addRow("Max Companies:", self.max_companies)
        
        self.browser_timeout = QSpinBox()
        self.browser_timeout.setRange(10, 120)
        self.browser_timeout.setValue(30)
        self.browser_timeout.setSuffix(" seconds")
        process_layout.addRow("Browser Timeout:", self.browser_timeout)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        # HubSpot Configuration
        hubspot_group = QGroupBox("HubSpot Configuration")
        hubspot_layout = QFormLayout()
        
        self.create_hubspot_contacts = QCheckBox()
        self.create_hubspot_contacts.setChecked(True)
        hubspot_layout.addRow("Create HubSpot Contacts:", self.create_hubspot_contacts)
        
        self.hubspot_owner_email = QLineEdit()
        self.hubspot_owner_email.setPlaceholderText("your-email@company.com")
        hubspot_layout.addRow("HubSpot Owner Email:", self.hubspot_owner_email)
        
        hubspot_group.setLayout(hubspot_layout)
        layout.addWidget(hubspot_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_settings)
        load_btn = QPushButton("Load from .env")
        load_btn.clicked.connect(self.load_from_env)
        test_btn = QPushButton("Test Configuration")
        test_btn.clicked.connect(self.test_configuration)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(load_btn)
        button_layout.addWidget(test_btn)
        layout.addLayout(button_layout)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Initial setup
        self.on_data_source_changed()
    
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
        """Load configuration from QSettings"""
        self.openai_key.setText(self.settings.value("openai_key", ""))
        self.hubspot_key.setText(self.settings.value("hubspot_key", ""))
        self.clearbit_key.setText(self.settings.value("clearbit_key", ""))
        self.data_source_type.setCurrentText(self.settings.value("data_source_type", "csv"))
        self.csv_file_path.setText(self.settings.value("csv_file_path", "companies.csv"))
        self.sheet_url.setText(self.settings.value("sheet_url", ""))
        self.worksheet_name.setText(self.settings.value("worksheet_name", ""))
        self.max_companies.setValue(int(self.settings.value("max_companies", 100)))
        self.browser_timeout.setValue(int(self.settings.value("browser_timeout", 30)))
        self.create_hubspot_contacts.setChecked(self.settings.value("create_hubspot_contacts", True, type=bool))
        self.hubspot_owner_email.setText(self.settings.value("hubspot_owner_email", ""))
        
        self.on_data_source_changed()
    
    def load_from_env(self):
        """Load configuration from .env file"""
        load_dotenv()
        
        self.openai_key.setText(os.getenv("OPENAI_API_KEY", ""))
        self.hubspot_key.setText(os.getenv("HUBSPOT_API_KEY", ""))
        self.clearbit_key.setText(os.getenv("CLEARBIT_API_KEY", ""))
        self.data_source_type.setCurrentText(os.getenv("DATA_SOURCE_TYPE", "csv"))
        self.csv_file_path.setText(os.getenv("CSV_FILE_PATH", "companies.csv"))
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
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        return {
            "openai_api_key": self.openai_key.text(),
            "data_source": {
                "type": self.data_source_type.currentText(),
                "file_path": self.csv_file_path.text() or "companies.csv",
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


class PromptsTab(QWidget):
    """Custom prompts configuration tab"""
    
    def __init__(self):
        super().__init__()
        self.custom_prompts = {}
        self.init_ui()
    
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
        load_btn = QPushButton("Load from File")
        load_btn.clicked.connect(self.load_prompts_file)
        save_btn = QPushButton("Save to File")
        save_btn.clicked.connect(self.save_prompts_file)
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_prompts)
        
        button_layout.addWidget(load_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Scrollable prompts area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.prompts_layout = QVBoxLayout()
        
        # Add prompt editors
        self.add_prompt_editor("Target Executives", "prospect_enricher_target_executives", 
                              "Define target executive roles to search for on LinkedIn")
        self.add_prompt_editor("Web Search Prompt", "web_enricher_system_prompt",
                              "System prompt for web search and analysis")
        self.add_prompt_editor("LinkedIn Search Instructions", "prospect_enricher_instructions",
                              "Instructions for LinkedIn prospect search")
        
        scroll_widget.setLayout(self.prompts_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
    
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
    
    def reset_prompts(self):
        """Reset all prompts to empty (use defaults)"""
        reply = QMessageBox.question(
            self, "Reset Prompts", 
            "Are you sure you want to reset all prompts to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.set_prompts({})
    
    def get_prompts(self) -> Dict[str, str]:
        """Get current custom prompts"""
        prompts = {}
        
        # Get text from all editors
        for attr_name in dir(self):
            if attr_name.endswith('_editor'):
                editor = getattr(self, attr_name)
                key = attr_name.replace('_editor', '')
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
        super().__init__()
        self.main_window = main_window
        self.workflow_thread = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Workflow")
        self.start_btn.clicked.connect(self.start_workflow)
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        
        self.stop_btn = QPushButton("Stop Workflow")
        self.stop_btn.clicked.connect(self.stop_workflow)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Status section
        status_group = QGroupBox("Workflow Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Ready to start")
        self.status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Progress log
        log_group = QGroupBox("Progress Log")
        log_layout = QVBoxLayout()
        
        self.progress_log = QTextEdit()
        self.progress_log.setReadOnly(True)
        self.progress_log.setMaximumHeight(200)
        log_layout.addWidget(self.progress_log)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Results summary
        results_group = QGroupBox("Results Summary")
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
                self.workflow_thread.stop()
                self.reset_ui()
                self.status_label.setText("Workflow stopped by user")
    
    @pyqtSlot(str)
    def update_progress(self, message):
        """Update progress log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.progress_log.append(f"[{timestamp}] {message}")
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
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
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
        self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        
        QMessageBox.critical(self, "Workflow Error", f"Workflow failed:\n\n{error_message}")
    
    def reset_ui(self):
        """Reset UI to initial state"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)


class ResultsTab(QWidget):
    """Results viewing and analysis tab"""
    
    def __init__(self):
        super().__init__()
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
        
        self.open_folder_btn = QPushButton("Open Results Folder")
        self.open_folder_btn.clicked.connect(self.open_results_folder)
        
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
        super().__init__()
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
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_logs)
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.auto_refresh_cb)
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(clear_btn)
        layout.addLayout(header_layout)
        
        # Log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_viewer)
        
        self.setLayout(layout)
    
    def toggle_auto_refresh(self, enabled):
        """Toggle auto-refresh of logs"""
        if enabled:
            self.timer.start(2000)  # Refresh every 2 seconds
        else:
            self.timer.stop()
    
    def manual_refresh(self):
        """Manually refresh logs"""
        self.refresh_logs()
    
    def refresh_logs(self):
        """Refresh log content"""
        # This is a placeholder - implement based on your logging system
        if self.current_log_file and os.path.exists(self.current_log_file):
            try:
                with open(self.current_log_file, 'r') as f:
                    content = f.read()
                    self.log_viewer.setPlainText(content)
                    # Scroll to bottom
                    self.log_viewer.moveCursor(QTextCursor.MoveOperation.End)
            except Exception as e:
                self.log_viewer.append(f"Error reading log file: {str(e)}")
    
    def clear_logs(self):
        """Clear log viewer"""
        self.log_viewer.clear()
    
    def set_log_file(self, log_file_path):
        """Set the current log file to monitor"""
        self.current_log_file = log_file_path
        self.refresh_logs()


class SDRMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("SDR Workflow - Advanced GUI")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.config_tab = ConfigurationTab()
        self.prompts_tab = PromptsTab()
        self.execution_tab = ExecutionTab(self)
        self.results_tab = ResultsTab()
        self.logs_tab = LogViewerTab()
        
        # Add tabs
        self.tab_widget.addTab(self.config_tab, "Configuration")
        self.tab_widget.addTab(self.prompts_tab, "Custom Prompts")
        self.tab_widget.addTab(self.execution_tab, "Execution")
        self.tab_widget.addTab(self.results_tab, "Results")
        self.tab_widget.addTab(self.logs_tab, "Logs")
        
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Apply styles
        self.apply_styles()
    
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
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About SDR Workflow",
            "SDR Workflow - Advanced GUI\n\n"
            "A comprehensive workflow for Sales Development Representatives\n"
            "featuring LinkedIn prospect enrichment and HubSpot integration.\n\n"
            "Built with PyQt6 and Python."
        )
    
    def apply_styles(self):
        """Apply custom styles to the application"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #e1e1e1;
            padding: 8px 12px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #2196F3;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QPushButton {
            padding: 8px 16px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: #f8f9fa;
        }
        
        QPushButton:hover {
            background-color: #e9ecef;
        }
        
        QPushButton:pressed {
            background-color: #dee2e6;
        }
        
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            padding: 4px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        
        QLineEdit:focus, QTextEdit:focus {
            border-color: #2196F3;
        }
        """
        
        self.setStyleSheet(style)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("SDR Workflow GUI")
    app.setOrganizationName("SDR Tools")
    
    # Create and show main window
    window = SDRMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()