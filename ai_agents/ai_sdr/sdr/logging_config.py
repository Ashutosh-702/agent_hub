"""
Enhanced Logging Configuration for SDR Workflow

Provides standardized logging format, levels, and utility functions
for cleaner and more readable logs across all SDR modules.
"""

import os
import sys
from typing import Dict, Any
from loguru import logger


class SDRLogger:
    """Enhanced logger for SDR workflow with standardized formatting"""

    def __init__(self):
        self.setup_done = False
        self.gui_callbacks = []  # Store GUI callback functions

    def add_gui_callback(self, callback):
        """Register a GUI callback function to receive log messages"""
        if callback not in self.gui_callbacks:
            self.gui_callbacks.append(callback)
    
    def remove_gui_callback(self, callback):
        """Remove a GUI callback function"""
        if callback in self.gui_callbacks:
            self.gui_callbacks.remove(callback)
    
    def _emit_to_gui(self, message):
        """Emit log messages to all registered GUI callbacks"""
        for callback in self.gui_callbacks:
            try:
                callback(message)
            except Exception:
                pass  # Silently ignore GUI callback errors

    def setup_enhanced_logging(self, run_directories: Dict[str, str] = None):
        """Configure enhanced logging for the workflow with better readability"""
        if self.setup_done:
            return

        logger.remove()

        # Console logging with enhanced format - standardized column widths
        def console_sink(message):
            """Custom sink that also emits to GUI callbacks"""
            # Emit to stdout
            sys.stdout.write(message)
            # Emit to GUI callbacks if any
            if self.gui_callbacks:
                self._emit_to_gui(message.record["message"])
        
        logger.add(
            console_sink,
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level:>8}</level> | <cyan>{extra[module]:>30}</cyan> "
                   "| <level>{message}</level>",
            level="INFO",
            colorize=True,
            filter=lambda record: record["extra"].update(module=record["name"].split(".")[-1]) or True
        )

        # File logging with detailed format if run directories provided
        if run_directories:
            # Store log file paths globally for easy access
            global _LOG_FILE_PATHS
            _LOG_FILE_PATHS["workflow"] = f"{run_directories['logs_dir']}/workflow.log"
            _LOG_FILE_PATHS["errors"] = f"{run_directories['logs_dir']}/errors.log"
            _LOG_FILE_PATHS["llm_requests"] = f"{run_directories['logs_dir']}/llm_requests.log"
            _LOG_FILE_PATHS["company_progress"] = f"{run_directories['logs_dir']}/company_progress.log"
            
            logger.add(
                _LOG_FILE_PATHS["workflow"],
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:>8} | {name:>30} | {function:>20} | {line:>4} | {"
                       "message}",
                level="DEBUG",
                # No rotation - infinite file size
                retention="30 days",
                enqueue=True,  # Enable thread-safe logging
                backtrace=True,  # Add backtrace for better debugging
                diagnose=True,  # Add diagnosis info
                colorize=False,  # No colors in file
                serialize=False  # Don't serialize to JSON
            )

            # Separate error log file
            logger.add(
                _LOG_FILE_PATHS["errors"],
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:>8} | {name:>30} | {function:>20} | {line:>4} | {"
                       "message}",
                level="ERROR",
                # No rotation - infinite file size
                retention="30 days",
                enqueue=True,
                backtrace=True,
                diagnose=True,
                colorize=False
            )

            # Separate LLM response log file (no console output)
            logger.add(
                _LOG_FILE_PATHS["llm_requests"],
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:>8} | {name:>30} | {function:>20} | {line:>4} | {"
                       "message}",
                level="DEBUG",
                filter=lambda record: "llm_response" in record["extra"] or "llm_request" in record["extra"],
                # No rotation - infinite file size
                retention="30 days",
                enqueue=True,
                colorize=False
            )

            # Company progress log file
            logger.add(
                _LOG_FILE_PATHS["company_progress"],
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:>8} | {name:>30} | {message}",
                level="INFO",
                filter=lambda record: "company_progress" in record["extra"],
                # No rotation - infinite file size
                retention="30 days",
                enqueue=True,
                colorize=False
            )

            logger.info(f"📊 Enhanced logging configured for run: {run_directories['run_id']}")
            logger.info(f"📄 Main log: {_LOG_FILE_PATHS['workflow']} (unlimited size)")
            logger.info(f"🚨 Error log: {_LOG_FILE_PATHS['errors']} (unlimited size)")
            logger.info(f"🤖 LLM requests: {_LOG_FILE_PATHS['llm_requests']} (unlimited size, file only)")
            logger.info(f"📈 Company progress: {_LOG_FILE_PATHS['company_progress']} (unlimited size, file only)")
            logger.info("")

        self.setup_done = True

    @staticmethod
    def log_section_start(title: str, subtitle: str = ""):
        """Log a clean section start with proper formatting"""
        logger.info("")
        logger.info("═" * 60)
        logger.info(f"🚀 {title}")
        if subtitle:
            logger.info(f"📋 {subtitle}")
        logger.info("═" * 60)

    @staticmethod
    def log_subsection(title: str, details: Dict[str, Any] = None):
        """Log a subsection with optional details"""
        logger.info("")
        logger.info("─" * 50)
        logger.info(f"▶️ {title}")
        logger.info("─" * 50)

        if details:
            for key, value in details.items():
                logger.info(f"   {key}: {value}")

    @staticmethod
    def log_progress(current: int, total: int, item_name: str = "item"):
        """Log progress in a clean format"""
        percentage = (current / total * 100) if total > 0 else 0
        logger.info(f"📊 Progress: {current}/{total} {item_name}s ({percentage:.1f}%)")

    @staticmethod
    def log_results(title: str, results: Dict[str, Any]):
        """Log results in a clean format"""
        logger.info("")
        logger.info(f"📊 {title}:")
        logger.info("─" * 40)
        for key, value in results.items():
            emoji = SDRLogger._get_result_emoji(key)
            logger.info(f"{emoji} {key}: {value}")

    @staticmethod
    def log_completion(title: str, summary: Dict[str, Any] = None):
        """Log completion with summary"""
        logger.info("")
        logger.info("✅ " + title + " completed successfully")

        if summary:
            logger.info("")
            for key, value in summary.items():
                emoji = SDRLogger._get_result_emoji(key)
                logger.info(f"{emoji} {key}: {value}")

    @staticmethod
    def log_error_with_context(error: Exception, context: str = ""):
        """Log error with proper context"""
        logger.error("")
        logger.error("❌ " + "ERROR ENCOUNTERED".center(50, "═"))
        if context:
            logger.error(f"📍 Context: {context}")
        logger.error(f"🚨 Error: {str(error)}")
        logger.error("═" * 50)

    @staticmethod
    def log_warning_with_context(message: str, context: str = ""):
        """Log warning with proper context"""
        if context:
            logger.warning(f"⚠️ {context}: {message}")
        else:
            logger.warning(f"⚠️ {message}")

    @staticmethod
    def log_api_usage(tokens: int, input_tokens: int = None, output_tokens: int = None):
        """Log API usage in a standardized format"""
        if input_tokens is not None and output_tokens is not None:
            logger.info(f"💰 API Usage: {tokens:,} tokens (Input: {input_tokens:,}, Output: {output_tokens:,})")
        else:
            logger.info(f"💰 API Usage: {tokens:,} tokens")

    @staticmethod
    def log_file_saved(filename: str, details: str = ""):
        """Log file saved operation"""
        if details:
            logger.info(f"💾 Saved: {filename} ({details})")
        else:
            logger.info(f"💾 Saved: {filename}")

    @staticmethod
    def log_processing_item(item_name: str, details: Dict[str, Any] = None):
        """Log processing of individual items"""
        logger.info("")
        logger.info("─" * 50)
        logger.info(f"🔍 Processing: {item_name}")
        logger.info("─" * 50)

        if details:
            for key, value in details.items():
                logger.info(f"   📌 {key}: {value}")

    @staticmethod
    def log_llm_request(model: str, prompt: str, context: str = ""):
        """Log LLM request (file only, no console)"""
        logger.bind(llm_response=True).info(f"🤖 LLM REQUEST | Model: {model} | Context: {context}")
        logger.bind(llm_response=True).info(f"📝 PROMPT: {prompt}")
        logger.bind(llm_response=True).info("─" * 100)

    @staticmethod
    def log_llm_response(model: str, response: str, context: str = "", tokens: int = None):
        """Log LLM response (file only, no console)"""
        logger.bind(llm_response=True).info(f"🤖 LLM RESPONSE | Model: {model} | Context: {context}")
        if tokens:
            logger.bind(llm_response=True).info(f"💰 Tokens used: {tokens:,}")
        logger.bind(llm_response=True).info(f"📤 RESPONSE: {response}")
        logger.bind(llm_response=True).info("═" * 100)

    @staticmethod
    def log_llm_error(model: str, error: str, context: str = ""):
        """Log LLM error (file only, no console)"""
        logger.bind(llm_response=True).error(f"🤖 LLM ERROR | Model: {model} | Context: {context}")
        logger.bind(llm_response=True).error(f"❌ ERROR: {error}")
        logger.bind(llm_response=True).error("═" * 100)

    @staticmethod
    def log_company_progress(company_name: str, step: str, status: str, details: Dict[str, Any] = None):
        """Log company processing progress to dedicated file"""
        message = f"Company: {company_name} | Step: {step} | Status: {status}"
        if details:
            details_str = " | " + " | ".join([f"{k}: {v}" for k, v in details.items()])
            message += details_str
        logger.bind(company_progress=True).info(message)
    
    @staticmethod
    def _get_result_emoji(key: str) -> str:
        """Get appropriate emoji for result keys"""
        key_lower = key.lower()

        if any(word in key_lower for word in ['success', 'created', 'found', 'processed']):
            return "✅"
        elif any(word in key_lower for word in ['failed', 'error', 'missing']):
            return "❌"
        elif any(word in key_lower for word in ['duplicate', 'skip', 'retry']):
            return "🔄"
        elif any(word in key_lower for word in ['total', 'count', 'number']):
            return "📊"
        elif any(word in key_lower for word in ['time', 'duration']):
            return "⏱️"
        elif any(word in key_lower for word in ['rate', 'percentage']):
            return "📈"
        else:
            return "📋"


# Global logger instance
sdr_logger = SDRLogger()

# Global variable for clean logging mode
_LOG_MODE = None

# Global variable for current log file paths
_LOG_FILE_PATHS = {
    "workflow": None,
    "errors": None,
    "llm_requests": None,
    "company_progress": None
}


def get_log_mode() -> str:
    """Get the current logging mode from environment"""
    global _LOG_MODE
    if _LOG_MODE is None:
        _LOG_MODE = os.getenv("LOG_MODE", "clean").lower()
    return _LOG_MODE


def clean_log(message: str, level: str = "info"):
    """Helper function for clean terminal logging"""
    if get_log_mode() == "clean":
        # Simple, clean message without excessive formatting
        getattr(logger, level)(message)
    else:
        # Detailed mode - use original verbose logging
        getattr(logger, level)(message)


def detailed_log(message: str, level: str = "info"):
    """Helper function for detailed logging (only shown in detailed mode)"""
    if get_log_mode() == "detailed":
        getattr(logger, level)(message)


def setup_sdr_logging(run_directories: Dict[str, str] = None):
    """Setup SDR logging configuration"""
    sdr_logger.setup_enhanced_logging(run_directories)


def register_gui_callback(callback):
    """Register a GUI callback to receive log messages"""
    sdr_logger.add_gui_callback(callback)


def unregister_gui_callback(callback):
    """Unregister a GUI callback"""
    sdr_logger.remove_gui_callback(callback)


def clear_all_gui_callbacks():
    """Clear all registered GUI callbacks"""
    sdr_logger.gui_callbacks.clear()


def get_gui_callback_count():
    """Get the number of registered GUI callbacks"""
    return len(sdr_logger.gui_callbacks)


def log_workflow_start(workflow_name: str, config: Dict[str, Any]):
    """Log workflow start with configuration summary"""
    sdr_logger.log_section_start(f"{workflow_name} Starting", "Configuration loaded successfully")

    config_summary = {
        "Data source": config.get("data_source", {}).get("type", "Unknown"),
        "OpenAI API": "✅ Configured" if config.get("openai_api_key") else "❌ Missing",
        "HubSpot API": "✅ Configured" if config.get("hubspot_api_key") else "⚠️ Optional",
        "HubSpot contacts": "✅ Enabled" if config.get("create_hubspot_contacts") else "❌ Disabled",
        "Custom prompts": "✅ Using custom" if config.get("custom_prompts") else "📝 Using defaults"
    }

    logger.info("")
    logger.info("⚙️ Configuration Summary:")
    logger.info("─" * 30)
    for key, value in config_summary.items():
        logger.info(f"   {key}: {value}")
    logger.info("")


def log_workflow_completion(total_time: float = None, final_stats: Dict[str, Any] = None):
    """Log workflow completion with final statistics"""
    logger.info("")
    logger.info("═" * 80)
    logger.info("🎉 WORKFLOW COMPLETED SUCCESSFULLY! 🎉")
    logger.info("═" * 80)

    if total_time:
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        logger.info(f"⏱️ Total execution time: {minutes}m {seconds}s")

    if final_stats:
        logger.info("")
        logger.info("📊 Final Statistics:")
        logger.info("─" * 30)
        for key, value in final_stats.items():
            emoji = SDRLogger._get_result_emoji(key)
            logger.info(f"{emoji} {key}: {value}")

    logger.info("")
    logger.info("📁 Click 'Open Output' to view results folder")
    logger.info("═" * 80)


# LLM logging convenience functions
def log_llm_request(model: str, prompt: str, context: str = ""):
    """Log LLM request to file only"""
    SDRLogger.log_llm_request(model, prompt, context)


def log_llm_response(model: str, response: str, context: str = "", tokens: int = None):
    """Log LLM response to file only"""
    SDRLogger.log_llm_response(model, response, context, tokens)


def log_llm_error(model: str, error: str, context: str = ""):
    """Log LLM error to file only"""
    SDRLogger.log_llm_error(model, error, context)


# Log file path access functions
def get_log_file_path(log_type: str = "workflow") -> str:
    """Get the path to a specific log file type"""
    return _LOG_FILE_PATHS.get(log_type)


def get_all_log_file_paths() -> Dict[str, str]:
    """Get all current log file paths"""
    return _LOG_FILE_PATHS.copy()


def set_log_file_path(log_type: str, path: str):
    """Set a log file path (for testing or custom setups)"""
    global _LOG_FILE_PATHS
    if log_type in _LOG_FILE_PATHS:
        _LOG_FILE_PATHS[log_type] = path


def clear_log_file_paths():
    """Clear all log file paths"""
    global _LOG_FILE_PATHS
    for key in _LOG_FILE_PATHS:
        _LOG_FILE_PATHS[key] = None


def prompt_log(message: str):
    """
    Custom logging function for prompt customization interface
    Provides clean output without timestamps for better user experience
    """
    print(message)
