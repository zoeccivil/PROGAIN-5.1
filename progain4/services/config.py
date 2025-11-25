"""
Configuration service for PROGAIN 5.1
Handles persistent storage of application settings using platform-appropriate mechanisms.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration manager that persists settings.
    Uses Windows Registry on Windows, or a JSON file on other platforms.
    """
    
    _instance = None
    _config_data: dict = {}
    
    # Registry key for Windows
    REGISTRY_KEY = r"SOFTWARE\PROGAIN\5.1"
    
    # JSON config file for other platforms
    CONFIG_DIR = Path.home() / ".progain"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_config()
        logger.info("Config initialized")
    
    def _is_windows(self) -> bool:
        """Check if running on Windows."""
        return sys.platform == 'win32'
    
    def _load_config(self) -> None:
        """Load configuration from storage."""
        if self._is_windows():
            self._load_from_registry()
        else:
            self._load_from_file()
    
    def _save_config(self) -> None:
        """Save configuration to storage."""
        if self._is_windows():
            self._save_to_registry()
        else:
            self._save_to_file()
    
    def _load_from_registry(self) -> None:
        """Load configuration from Windows Registry."""
        try:
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY)
                try:
                    value, _ = winreg.QueryValueEx(key, "config")
                    self._config_data = json.loads(value)
                    logger.debug("Config loaded from registry")
                except FileNotFoundError:
                    self._config_data = {}
                finally:
                    winreg.CloseKey(key)
            except FileNotFoundError:
                self._config_data = {}
                logger.debug("Registry key not found, using defaults")
        except ImportError:
            logger.warning("winreg not available, falling back to file storage")
            self._load_from_file()
    
    def _save_to_registry(self) -> None:
        """Save configuration to Windows Registry."""
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY)
            winreg.SetValueEx(key, "config", 0, winreg.REG_SZ, json.dumps(self._config_data))
            winreg.CloseKey(key)
            logger.debug("Config saved to registry")
        except ImportError:
            logger.warning("winreg not available, falling back to file storage")
            self._save_to_file()
        except Exception as e:
            logger.error(f"Failed to save config to registry: {e}")
    
    def _load_from_file(self) -> None:
        """Load configuration from JSON file."""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
                    logger.debug(f"Config loaded from {self.CONFIG_FILE}")
            else:
                self._config_data = {}
                logger.debug("Config file not found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load config from file: {e}")
            self._config_data = {}
    
    def _save_to_file(self) -> None:
        """Save configuration to JSON file."""
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2)
            logger.debug(f"Config saved to {self.CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to save config to file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save."""
        self._config_data[key] = value
        self._save_config()
        logger.debug(f"Config set: {key} = {value}")
    
    def delete(self, key: str) -> None:
        """Delete a configuration value."""
        if key in self._config_data:
            del self._config_data[key]
            self._save_config()
            logger.debug(f"Config deleted: {key}")
    
    # Theme-specific methods (Task 3)
    def get_theme(self) -> Optional[str]:
        """Get the saved theme name."""
        return self.get("theme")
    
    def set_theme(self, theme_name: str) -> None:
        """Save the theme name."""
        self.set("theme", theme_name)
        logger.info(f"Theme saved: {theme_name}")
    
    # Last project methods
    def get_last_project_id(self) -> Optional[str]:
        """Get the last selected project ID."""
        return self.get("last_project_id")
    
    def set_last_project_id(self, project_id: str) -> None:
        """Save the last selected project ID."""
        self.set("last_project_id", project_id)


# Singleton instance for easy import
config = Config()
