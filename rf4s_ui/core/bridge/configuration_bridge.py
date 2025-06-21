#!/usr/bin/env python3
"""
RF4S Configuration Bridge - Non-invasive Configuration Management

This bridge provides read/write access to RF4S configuration files without
modifying the RF4S source code. It handles various configuration formats
and maintains compatibility with the existing RF4S configuration system.

Features:
- Read/write YAML, JSON, and INI configuration files
- Configuration validation and backup
- Real-time configuration monitoring
- Non-invasive configuration updates
- Configuration history tracking
"""

import configparser
import json
import logging
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ConfigurationBridge:
    """
    Non-invasive bridge for RF4S configuration management

    This bridge allows the UI to read and write RF4S configuration files
    without modifying the RF4S source code. It supports multiple configuration
    formats and provides validation and backup capabilities.
    """

    def __init__(self, rf4s_path: Optional[Path] = None):
        self.rf4s_path = rf4s_path or self._find_rf4s_installation()
        self.config_path = (
            self.rf4s_path / "config" if self.rf4s_path else Path("config")
        )
        self.backup_path = self.config_path / "backups"
        self.observers = {}
        self.config_cache = {}
        self.change_callbacks = {}
        self.logger = logging.getLogger(__name__)

        # Ensure backup directory exists
        self.backup_path.mkdir(parents=True, exist_ok=True)

    def _find_rf4s_installation(self) -> Optional[Path]:
        """Find RF4S installation directory"""
        possible_paths = [
            Path("C:/RF4S"),
            Path("C:/RussianFishing4Script"),
            Path.home() / "RF4S",
            Path.cwd().parent / "rf4s",
            Path("C:/Users") / os.getenv("USERNAME", "") / "RF4S",
        ]

        for path in possible_paths:
            if path.exists() and (path / "rf4s").exists():
                return path

        return None

    def read_config(
        self, config_name: str, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Read configuration file

        Args:
            config_name: Name of the configuration file (without extension)
            use_cache: Whether to use cached configuration

        Returns:
            Configuration dictionary or None if not found
        """
        try:
            if use_cache and config_name in self.config_cache:
                return self.config_cache[config_name].copy()

            config_file = self._find_config_file(config_name)
            if not config_file:
                self.logger.warning(f"Configuration file not found: {config_name}")
                return None

            config_data = self._read_config_file(config_file)
            if config_data is not None:
                self.config_cache[config_name] = config_data.copy()

            return config_data

        except Exception as e:
            self.logger.error(f"Error reading config {config_name}: {e}")
            return None

    def write_config(
        self, config_name: str, config_data: Dict[str, Any], create_backup: bool = True
    ) -> bool:
        """
        Write configuration file

        Args:
            config_name: Name of the configuration file
            config_data: Configuration data to write
            create_backup: Whether to create a backup before writing

        Returns:
            True if successful, False otherwise
        """
        try:
            config_file = self._find_config_file(config_name)
            if not config_file:
                # Try to determine file format and create new file
                config_file = self._create_config_file(config_name, config_data)
                if not config_file:
                    return False

            # Create backup if requested and file exists
            if create_backup and config_file.exists():
                self._create_backup(config_file)

            # Write configuration
            success = self._write_config_file(config_file, config_data)
            if success:
                self.config_cache[config_name] = config_data.copy()
                self._notify_config_change(config_name, config_data)

            return success

        except Exception as e:
            self.logger.error(f"Error writing config {config_name}: {e}")
            return False

    def _find_config_file(self, config_name: str) -> Optional[Path]:
        """Find configuration file with various extensions"""
        extensions = [".yaml", ".yml", ".json", ".ini", ".cfg"]

        for ext in extensions:
            config_file = self.config_path / f"{config_name}{ext}"
            if config_file.exists():
                return config_file

        return None

    def _create_config_file(
        self, config_name: str, config_data: Dict[str, Any]
    ) -> Optional[Path]:
        """Create new configuration file"""
        try:
            # Default to YAML format for new files
            config_file = self.config_path / f"{config_name}.yaml"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            return config_file
        except Exception as e:
            self.logger.error(f"Error creating config file {config_name}: {e}")
            return None

    def _read_config_file(self, config_file: Path) -> Optional[Dict[str, Any]]:
        """Read configuration file based on its extension"""
        try:
            extension = config_file.suffix.lower()

            with open(config_file, "r", encoding="utf-8") as f:
                if extension in [".yaml", ".yml"]:
                    return yaml.safe_load(f) or {}
                elif extension == ".json":
                    return json.load(f) or {}
                elif extension in [".ini", ".cfg"]:
                    config = configparser.ConfigParser()
                    config.read_string(f.read())
                    return {
                        section: dict(config[section]) for section in config.sections()
                    }
                else:
                    self.logger.warning(f"Unsupported config format: {extension}")
                    return None

        except Exception as e:
            self.logger.error(f"Error reading config file {config_file}: {e}")
            return None

    def _write_config_file(
        self, config_file: Path, config_data: Dict[str, Any]
    ) -> bool:
        """Write configuration file based on its extension"""
        try:
            extension = config_file.suffix.lower()

            with open(config_file, "w", encoding="utf-8") as f:
                if extension in [".yaml", ".yml"]:
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
                elif extension == ".json":
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                elif extension in [".ini", ".cfg"]:
                    config = configparser.ConfigParser()
                    for section, values in config_data.items():
                        config[section] = values
                    config.write(f)
                else:
                    self.logger.warning(f"Unsupported config format: {extension}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error writing config file {config_file}: {e}")
            return False

    def _create_backup(self, config_file: Path) -> bool:
        """Create backup of configuration file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_file.stem}_{timestamp}{config_file.suffix}"
            backup_file = self.backup_path / backup_name

            shutil.copy2(config_file, backup_file)
            self.logger.info(f"Created backup: {backup_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating backup for {config_file}: {e}")
            return False

    def get_config_list(self) -> List[str]:
        """Get list of available configuration files"""
        try:
            if not self.config_path.exists():
                return []

            config_files = []
            extensions = [".yaml", ".yml", ".json", ".ini", ".cfg"]

            for file_path in self.config_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    config_files.append(file_path.stem)

            return sorted(config_files)

        except Exception as e:
            self.logger.error(f"Error getting config list: {e}")
            return []

    def validate_config(
        self, config_name: str, config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate configuration data

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
        }

        try:
            # Basic validation checks
            if not isinstance(config_data, dict):
                validation_result["valid"] = False
                validation_result["errors"].append("Configuration must be a dictionary")
                return validation_result

            # Check for required fields based on config type
            if config_name == "config":
                self._validate_main_config(config_data, validation_result)
            elif config_name == "settings":
                self._validate_settings_config(config_data, validation_result)

            # Check for common issues
            self._validate_common_issues(config_data, validation_result)

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {e}")

        return validation_result

    def _validate_main_config(
        self, config_data: Dict[str, Any], result: Dict[str, Any]
    ):
        """Validate main configuration file"""
        required_fields = ["version"]

        for field in required_fields:
            if field not in config_data:
                result["warnings"].append(f"Missing recommended field: {field}")

    def _validate_settings_config(
        self, config_data: Dict[str, Any], result: Dict[str, Any]
    ):
        """Validate settings configuration file"""
        # Add specific settings validation logic here
        pass

    def _validate_common_issues(
        self, config_data: Dict[str, Any], result: Dict[str, Any]
    ):
        """Check for common configuration issues"""
        # Check for empty values
        for key, value in config_data.items():
            if value == "":
                result["warnings"].append(f"Empty value for key: {key}")

    def start_monitoring(self, config_name: str, callback):
        """Start monitoring configuration file for changes"""
        try:
            config_file = self._find_config_file(config_name)
            if not config_file:
                self.logger.warning(
                    f"Cannot monitor non-existent config: {config_name}"
                )
                return False

            if config_name in self.observers:
                self.stop_monitoring(config_name)

            event_handler = ConfigFileHandler(config_file, callback)
            observer = Observer()
            observer.schedule(event_handler, str(config_file.parent), recursive=False)
            observer.start()

            self.observers[config_name] = observer
            self.change_callbacks[config_name] = callback

            self.logger.info(f"Started monitoring config: {config_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error starting monitoring for {config_name}: {e}")
            return False

    def stop_monitoring(self, config_name: str):
        """Stop monitoring configuration file"""
        try:
            if config_name in self.observers:
                self.observers[config_name].stop()
                self.observers[config_name].join()
                del self.observers[config_name]

            if config_name in self.change_callbacks:
                del self.change_callbacks[config_name]

            self.logger.info(f"Stopped monitoring config: {config_name}")

        except Exception as e:
            self.logger.error(f"Error stopping monitoring for {config_name}: {e}")

    def _notify_config_change(self, config_name: str, config_data: Dict[str, Any]):
        """Notify registered callbacks of configuration changes"""
        if config_name in self.change_callbacks:
            try:
                self.change_callbacks[config_name](config_name, config_data)
            except Exception as e:
                self.logger.error(
                    f"Error in config change callback for {config_name}: {e}"
                )

    def get_backup_list(self, config_name: str) -> List[Dict[str, Any]]:
        """Get list of backups for a configuration file"""
        try:
            backups = []
            pattern = f"{config_name}_*"

            for backup_file in self.backup_path.glob(pattern):
                if backup_file.is_file():
                    stat = backup_file.stat()
                    backups.append(
                        {
                            "name": backup_file.name,
                            "path": str(backup_file),
                            "size": stat.st_size,
                            "created": datetime.fromtimestamp(stat.st_ctime),
                            "modified": datetime.fromtimestamp(stat.st_mtime),
                        }
                    )

            return sorted(backups, key=lambda x: x["created"], reverse=True)

        except Exception as e:
            self.logger.error(f"Error getting backup list for {config_name}: {e}")
            return []

    def restore_backup(self, config_name: str, backup_name: str) -> bool:
        """Restore configuration from backup"""
        try:
            backup_file = self.backup_path / backup_name
            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_name}")
                return False

            config_file = self._find_config_file(config_name)
            if not config_file:
                self.logger.error(f"Config file not found: {config_name}")
                return False

            # Create backup of current file before restoring
            self._create_backup(config_file)

            # Restore from backup
            shutil.copy2(backup_file, config_file)

            # Clear cache to force reload
            if config_name in self.config_cache:
                del self.config_cache[config_name]

            self.logger.info(f"Restored config {config_name} from backup {backup_name}")
            return True

        except Exception as e:
            self.logger.error(
                f"Error restoring backup {backup_name} for {config_name}: {e}"
            )
            return False

    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop all monitoring
            for config_name in list(self.observers.keys()):
                self.stop_monitoring(config_name)

            # Clear caches
            self.config_cache.clear()
            self.change_callbacks.clear()

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration file monitoring"""

    def __init__(self, config_file: Path, callback):
        self.config_file = config_file
        self.callback = callback
        self.logger = logging.getLogger(__name__)

    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and Path(event.src_path) == self.config_file:
            try:
                self.callback(self.config_file.stem, None)
            except Exception as e:
                self.logger.error(f"Error in config file callback: {e}")
