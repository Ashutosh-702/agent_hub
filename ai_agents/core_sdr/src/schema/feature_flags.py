import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FeatureFlags:
    """Centralized feature flag management for schema updates."""
    
    def __init__(self, config_file: str = "config/system_config.json"):
        self.config_file = Path(config_file)
        self._flags_cache: Optional[Dict[str, bool]] = None
        self._load_flags()
    
    def _load_flags(self) -> None:
        """Load feature flags from config file and environment variables."""
        try:
            with open(self.config_file) as f:
                config = json.load(f)
            
            file_flags = config.get("feature_flags", {})
            
            # Environment variables override config file
            self._flags_cache = {
                "schema_auto_update": self._get_flag_value(
                    "SCHEMA_AUTO_UPDATE", 
                    file_flags.get("schema_auto_update", False)
                ),
                "schema_api_driven_updates": self._get_flag_value(
                    "SCHEMA_API_DRIVEN_UPDATES", 
                    file_flags.get("schema_api_driven_updates", False)
                ),
                "schema_scheduled_updates": self._get_flag_value(
                    "SCHEMA_SCHEDULED_UPDATES", 
                    file_flags.get("schema_scheduled_updates", False)
                )
            }
            
            logger.debug(f"Loaded feature flags: {self._flags_cache}")
            
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            self._flags_cache = {
                "schema_auto_update": False,
                "schema_api_driven_updates": False,
                "schema_scheduled_updates": False
            }
        except Exception as e:
            logger.error(f"Error loading feature flags: {e}")
            self._flags_cache = {
                "schema_auto_update": False,
                "schema_api_driven_updates": False,
                "schema_scheduled_updates": False
            }
    
    def _get_flag_value(self, env_var: str, config_default: bool) -> bool:
        """Get flag value from environment variable or config default."""
        env_value = os.getenv(env_var, "").lower()
        if env_value in ("true", "1", "yes", "on"):
            return True
        elif env_value in ("false", "0", "no", "off"):
            return False
        else:
            return config_default
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled."""
        if self._flags_cache is None:
            self._load_flags()
        
        return self._flags_cache.get(flag_name, False)
    
    def schema_auto_update_enabled(self) -> bool:
        """Check if schema auto-update is enabled (master switch)."""
        return self.is_enabled("schema_auto_update")
    
    def api_driven_updates_enabled(self) -> bool:
        """Check if API-driven updates are enabled."""
        return (self.schema_auto_update_enabled() and 
                self.is_enabled("schema_api_driven_updates"))
    
    def scheduled_updates_enabled(self) -> bool:
        """Check if scheduled updates are enabled."""
        return (self.schema_auto_update_enabled() and 
                self.is_enabled("schema_scheduled_updates"))
    
    def reload(self) -> None:
        """Reload feature flags from config file."""
        self._flags_cache = None
        self._load_flags()
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all current feature flag values."""
        if self._flags_cache is None:
            self._load_flags()
        return self._flags_cache.copy()
    
    def log_status(self) -> None:
        """Log current feature flag status."""
        flags = self.get_all_flags()
        logger.info("Feature Flag Status:")
        for flag, enabled in flags.items():
            status = "ENABLED" if enabled else "DISABLED"
            logger.info(f"  {flag}: {status}")
            
        # Log derived flags
        logger.info("Derived Flags:")
        logger.info(f"  API-driven updates: {'ENABLED' if self.api_driven_updates_enabled() else 'DISABLED'}")
        logger.info(f"  Scheduled updates: {'ENABLED' if self.scheduled_updates_enabled() else 'DISABLED'}")