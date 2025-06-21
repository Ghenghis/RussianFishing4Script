#!/usr/bin/env python3
"""
RF4S UI - Settings Manager

This module provides comprehensive settings management for the RF4S UI application.
Handles configuration persistence, validation, profile management, and backup/restore.

Features:
- Hierarchical settings organization
- Configuration validation and type checking
- Profile-based settings management
- Backup and restore capabilities
- Import/export functionality
- Real-time settings monitoring
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PyQt6.QtCore import QObject, QSettings, pyqtSignal

from ...core.service_registry import ServiceRegistry


class SettingsManager(QObject):
    """
    Comprehensive settings management system

    This manager handles all application settings including UI preferences,
    panel configurations, theme settings, and user profiles.
    """

    # Signals
    setting_changed = pyqtSignal(str, object)  # key, value
    profile_changed = pyqtSignal(str)  # profile_name
    settings_loaded = pyqtSignal()
    settings_saved = pyqtSignal()

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__()

        self.service_registry = service_registry

        # Settings storage
        self.qt_settings = QSettings("RF4S", "RF4S-UI")
        self.current_profile = "default"
        self.settings_cache: Dict[str, Any] = {}

        # Settings structure
        self.settings_schema = self._create_settings_schema()

        # File paths
        self.settings_dir = Path.home() / ".rf4s_ui"
        self.profiles_dir = self.settings_dir / "profiles"
        self.backups_dir = self.settings_dir / "backups"

        # Initialize directories
        self._ensure_directories()

        # Load settings
        self._load_settings()

    def _create_settings_schema(self) -> Dict[str, Dict[str, Any]]:
        """Create the settings schema with validation rules"""
        return {
            "ui": {
                "window_geometry": {"type": "bytes", "default": b""},
                "window_state": {"type": "bytes", "default": b""},
                "panel_layout": {"type": "str", "default": "2-panel"},
                "panel_assignments": {
                    "type": "list",
                    "default": ["dashboard", "configuration"],
                },
                "splitter_sizes": {"type": "list", "default": [50, 50]},
                "show_toolbar": {"type": "bool", "default": True},
                "show_statusbar": {"type": "bool", "default": True},
                "auto_save_layout": {"type": "bool", "default": True},
            },
            "theme": {
                "current_theme": {"type": "str", "default": "auto"},
                "accent_color": {"type": "str", "default": "blue"},
                "custom_themes": {"type": "dict", "default": {}},
                "font_family": {"type": "str", "default": "Segoe UI"},
                "font_size": {"type": "int", "default": 9, "min": 8, "max": 16},
            },
            "panels": {
                "dashboard_refresh_rate": {
                    "type": "int",
                    "default": 1000,
                    "min": 100,
                    "max": 10000,
                },
                "monitoring_history_size": {
                    "type": "int",
                    "default": 1000,
                    "min": 100,
                    "max": 10000,
                },
                "log_max_lines": {
                    "type": "int",
                    "default": 1000,
                    "min": 100,
                    "max": 50000,
                },
                "auto_scroll_logs": {"type": "bool", "default": True},
                "show_timestamps": {"type": "bool", "default": True},
            },
            "rf4s": {
                "auto_connect": {"type": "bool", "default": False},
                "config_file_path": {"type": "str", "default": ""},
                "script_directory": {"type": "str", "default": ""},
                "backup_configs": {"type": "bool", "default": True},
                "monitor_changes": {"type": "bool", "default": True},
            },
            "notifications": {
                "enable_notifications": {"type": "bool", "default": True},
                "notification_sound": {"type": "bool", "default": True},
                "show_system_notifications": {"type": "bool", "default": True},
                "notification_duration": {
                    "type": "int",
                    "default": 5000,
                    "min": 1000,
                    "max": 30000,
                },
            },
            "performance": {
                "enable_animations": {"type": "bool", "default": True},
                "reduce_cpu_usage": {"type": "bool", "default": False},
                "memory_limit_mb": {
                    "type": "int",
                    "default": 512,
                    "min": 128,
                    "max": 2048,
                },
                "auto_cleanup": {"type": "bool", "default": True},
            },
            "advanced": {
                "debug_mode": {"type": "bool", "default": False},
                "log_level": {"type": "str", "default": "INFO"},
                "auto_diagnostics": {"type": "bool", "default": True},
                "crash_reporting": {"type": "bool", "default": True},
                "telemetry": {"type": "bool", "default": False},
            },
        }

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for directory in [self.settings_dir, self.profiles_dir, self.backups_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_settings(self):
        """Load settings from storage"""
        try:
            # Load from QSettings
            for category, settings in self.settings_schema.items():
                for key, config in settings.items():
                    full_key = f"{category}/{key}"
                    value = self.qt_settings.value(full_key, config["default"])

                    # Type conversion
                    if config["type"] == "bool" and isinstance(value, str):
                        value = value.lower() == "true"
                    elif config["type"] == "int" and isinstance(value, str):
                        try:
                            value = int(value)
                        except ValueError:
                            value = config["default"]
                    elif config["type"] == "list" and isinstance(value, str):
                        try:
                            value = json.loads(value) if value else config["default"]
                        except json.JSONDecodeError:
                            value = config["default"]
                    elif config["type"] == "dict" and isinstance(value, str):
                        try:
                            value = json.loads(value) if value else config["default"]
                        except json.JSONDecodeError:
                            value = config["default"]

                    self.settings_cache[full_key] = value

            # Load current profile
            self.current_profile = self.qt_settings.value("current_profile", "default")

            self.settings_loaded.emit()

        except Exception as e:
            print(f"Error loading settings: {e}")
            self._load_defaults()

    def _load_defaults(self):
        """Load default settings"""
        for category, settings in self.settings_schema.items():
            for key, config in settings.items():
                full_key = f"{category}/{key}"
                self.settings_cache[full_key] = config["default"]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings_cache.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set a setting value"""
        try:
            # Validate the setting
            if not self._validate_setting(key, value):
                return False

            # Update cache
            old_value = self.settings_cache.get(key)
            self.settings_cache[key] = value

            # Save to QSettings
            if isinstance(value, (list, dict)):
                self.qt_settings.setValue(key, json.dumps(value))
            else:
                self.qt_settings.setValue(key, value)

            # Emit signal if value changed
            if old_value != value:
                self.setting_changed.emit(key, value)

            return True

        except Exception as e:
            print(f"Error setting {key}: {e}")
            return False

    def _validate_setting(self, key: str, value: Any) -> bool:
        """Validate a setting value against schema"""
        # Find the setting in schema
        parts = key.split("/")
        if len(parts) != 2:
            return False

        category, setting_key = parts
        if category not in self.settings_schema:
            return False

        if setting_key not in self.settings_schema[category]:
            return False

        config = self.settings_schema[category][setting_key]

        # Type validation
        expected_type = config["type"]
        if expected_type == "bool" and not isinstance(value, bool):
            return False
        elif expected_type == "int" and not isinstance(value, int):
            return False
        elif expected_type == "str" and not isinstance(value, str):
            return False
        elif expected_type == "list" and not isinstance(value, list):
            return False
        elif expected_type == "dict" and not isinstance(value, dict):
            return False
        elif expected_type == "bytes" and not isinstance(value, bytes):
            return False

        # Range validation for integers
        if expected_type == "int":
            if "min" in config and value < config["min"]:
                return False
            if "max" in config and value > config["max"]:
                return False

        return True

    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all settings for a category"""
        result = {}
        for key, value in self.settings_cache.items():
            if key.startswith(f"{category}/"):
                setting_key = key.split("/", 1)[1]
                result[setting_key] = value
        return result

    def set_category(self, category: str, settings: Dict[str, Any]) -> bool:
        """Set multiple settings for a category"""
        success = True
        for key, value in settings.items():
            full_key = f"{category}/{key}"
            if not self.set(full_key, value):
                success = False
        return success

    def reset_category(self, category: str):
        """Reset a category to default values"""
        if category not in self.settings_schema:
            return

        for key, config in self.settings_schema[category].items():
            full_key = f"{category}/{key}"
            self.set(full_key, config["default"])

    def reset_all(self):
        """Reset all settings to defaults"""
        for category in self.settings_schema.keys():
            self.reset_category(category)

    def save_profile(self, profile_name: str) -> bool:
        """Save current settings as a profile"""
        try:
            profile_file = self.profiles_dir / f"{profile_name}.json"

            profile_data = {
                "name": profile_name,
                "created": datetime.now().isoformat(),
                "settings": dict(self.settings_cache),
            }

            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving profile {profile_name}: {e}")
            return False

    def load_profile(self, profile_name: str) -> bool:
        """Load settings from a profile"""
        try:
            profile_file = self.profiles_dir / f"{profile_name}.json"

            if not profile_file.exists():
                return False

            with open(profile_file, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

            # Load settings
            settings = profile_data.get("settings", {})
            for key, value in settings.items():
                self.set(key, value)

            self.current_profile = profile_name
            self.qt_settings.setValue("current_profile", profile_name)

            self.profile_changed.emit(profile_name)
            return True

        except Exception as e:
            print(f"Error loading profile {profile_name}: {e}")
            return False

    def get_profiles(self) -> List[str]:
        """Get list of available profiles"""
        profiles = []
        for profile_file in self.profiles_dir.glob("*.json"):
            profiles.append(profile_file.stem)
        return sorted(profiles)

    def delete_profile(self, profile_name: str) -> bool:
        """Delete a profile"""
        if profile_name == "default":
            return False  # Can't delete default profile

        try:
            profile_file = self.profiles_dir / f"{profile_name}.json"
            if profile_file.exists():
                profile_file.unlink()
                return True
            return False

        except Exception as e:
            print(f"Error deleting profile {profile_name}: {e}")
            return False

    def create_backup(self, name: Optional[str] = None) -> bool:
        """Create a backup of current settings"""
        try:
            if name is None:
                name = datetime.now().strftime("backup_%Y%m%d_%H%M%S")

            backup_file = self.backups_dir / f"{name}.json"

            backup_data = {
                "name": name,
                "created": datetime.now().isoformat(),
                "current_profile": self.current_profile,
                "settings": dict(self.settings_cache),
                "profiles": {},
            }

            # Include all profiles in backup
            for profile_name in self.get_profiles():
                profile_file = self.profiles_dir / f"{profile_name}.json"
                if profile_file.exists():
                    with open(profile_file, "r", encoding="utf-8") as f:
                        backup_data["profiles"][profile_name] = json.load(f)

            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def restore_backup(self, backup_name: str) -> bool:
        """Restore settings from a backup"""
        try:
            backup_file = self.backups_dir / f"{backup_name}.json"

            if not backup_file.exists():
                return False

            with open(backup_file, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            # Restore settings
            settings = backup_data.get("settings", {})
            for key, value in settings.items():
                self.set(key, value)

            # Restore profiles
            profiles = backup_data.get("profiles", {})
            for profile_name, profile_data in profiles.items():
                profile_file = self.profiles_dir / f"{profile_name}.json"
                with open(profile_file, "w", encoding="utf-8") as f:
                    json.dump(profile_data, f, indent=2, ensure_ascii=False)

            # Restore current profile
            current_profile = backup_data.get("current_profile", "default")
            self.current_profile = current_profile
            self.qt_settings.setValue("current_profile", current_profile)

            self.profile_changed.emit(current_profile)
            return True

        except Exception as e:
            print(f"Error restoring backup {backup_name}: {e}")
            return False

    def get_backups(self) -> List[Dict[str, str]]:
        """Get list of available backups"""
        backups = []
        for backup_file in self.backups_dir.glob("*.json"):
            try:
                with open(backup_file, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)

                backups.append(
                    {
                        "name": backup_file.stem,
                        "created": backup_data.get("created", "Unknown"),
                        "size": backup_file.stat().st_size,
                    }
                )
            except:
                continue

        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def export_settings(self, file_path: str) -> bool:
        """Export settings to a file"""
        try:
            export_data = {
                "exported": datetime.now().isoformat(),
                "version": "1.0",
                "current_profile": self.current_profile,
                "settings": dict(self.settings_cache),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False

    def import_settings(self, file_path: str) -> bool:
        """Import settings from a file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            # Validate format
            if "settings" not in import_data:
                return False

            # Import settings
            settings = import_data["settings"]
            for key, value in settings.items():
                if self._validate_setting(key, value):
                    self.set(key, value)

            return True

        except Exception as e:
            print(f"Error importing settings: {e}")
            return False

    def sync(self):
        """Synchronize settings to storage"""
        try:
            self.qt_settings.sync()
            self.settings_saved.emit()
        except Exception as e:
            print(f"Error syncing settings: {e}")

    def cleanup(self):
        """Cleanup settings manager"""
        self.sync()

        # Clean old backups (keep last 10)
        backups = self.get_backups()
        if len(backups) > 10:
            for backup in backups[10:]:
                backup_file = self.backups_dir / f"{backup['name']}.json"
                try:
                    backup_file.unlink()
                except:
                    pass


if __name__ == "__main__":
    # Test settings manager
    from ...core.service_registry import ServiceRegistry

    service_registry = ServiceRegistry()
    settings_manager = SettingsManager(service_registry)

    # Test basic operations
    print("Testing settings manager...")

    # Set some values
    settings_manager.set("ui/panel_layout", "3-panel")
    settings_manager.set("theme/current_theme", "dark")

    # Get values
    print(f"Panel layout: {settings_manager.get('ui/panel_layout')}")
    print(f"Theme: {settings_manager.get('theme/current_theme')}")

    # Test profile operations
    settings_manager.save_profile("test_profile")
    profiles = settings_manager.get_profiles()
    print(f"Available profiles: {profiles}")

    # Test backup
    settings_manager.create_backup("test_backup")
    backups = settings_manager.get_backups()
    print(f"Available backups: {len(backups)}")

    print("Settings manager test completed")
