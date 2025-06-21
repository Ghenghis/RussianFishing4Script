#!/usr/bin/env python3
"""
RF4S File Monitor Bridge - Non-invasive File System Monitoring

This bridge provides file system monitoring capabilities for RF4S without
modifying its source code. It monitors logs, screenshots, configuration files,
and other RF4S-related files for changes and provides real-time updates.

Features:
- Real-time file system monitoring
- Log file parsing and analysis
- Screenshot detection and processing
- Configuration file change detection
- Session data monitoring
- Non-invasive file access
"""

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from PIL import Image
from watchdog.events import (FileCreatedEvent, FileDeletedEvent,
                             FileModifiedEvent, FileSystemEventHandler)
from watchdog.observers import Observer


@dataclass
class FileChangeEvent:
    """Information about a file change event"""

    event_type: str  # 'created', 'modified', 'deleted'
    file_path: Path
    file_type: str  # 'log', 'screenshot', 'config', 'session', 'other'
    timestamp: datetime
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FileMonitorBridge:
    """
    Non-invasive bridge for RF4S file system monitoring

    This bridge monitors RF4S files and directories for changes without
    modifying the RF4S source code. It provides real-time file monitoring,
    log parsing, and file analysis capabilities.
    """

    def __init__(self, rf4s_path: Optional[Path] = None):
        self.rf4s_path = rf4s_path or self._find_rf4s_installation()
        self.observers = {}
        self.event_callbacks = {}
        self.monitoring_active = False
        self.logger = logging.getLogger(__name__)

        # File type patterns
        self.file_patterns = {
            "log": [".log", ".txt"],
            "screenshot": [".png", ".jpg", ".jpeg", ".bmp"],
            "config": [".yaml", ".yml", ".json", ".ini", ".cfg"],
            "session": [".session", ".data", ".save"],
            "template": [".template", ".tmpl"],
        }

        # Monitoring paths
        self.monitor_paths = self._get_monitor_paths()

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

    def _get_monitor_paths(self) -> Dict[str, Path]:
        """Get paths to monitor for different file types"""
        base_path = self.rf4s_path or Path.cwd()

        return {
            "logs": base_path / "logs",
            "screenshots": base_path / "screenshots",
            "config": base_path / "config",
            "session": base_path / "session",
            "templates": base_path / "templates",
            "data": base_path / "data",
            "temp": base_path / "temp",
        }

    def start_monitoring(
        self, paths: Optional[List[str]] = None, callback: Optional[Callable] = None
    ):
        """Start monitoring specified paths"""
        try:
            if self.monitoring_active:
                self.logger.warning("File monitoring is already active")
                return

            # Use all paths if none specified
            if paths is None:
                paths = list(self.monitor_paths.keys())

            # Register callback
            if callback:
                self.event_callbacks["default"] = callback

            # Start monitoring each path
            for path_name in paths:
                if path_name in self.monitor_paths:
                    self._start_path_monitoring(path_name)

            self.monitoring_active = True
            self.logger.info(f"Started file monitoring for paths: {paths}")

        except Exception as e:
            self.logger.error(f"Error starting file monitoring: {e}")

    def stop_monitoring(self):
        """Stop all file monitoring"""
        try:
            self.monitoring_active = False

            # Stop all observers
            for path_name, observer in self.observers.items():
                observer.stop()
                observer.join(timeout=5)
                self.logger.info(f"Stopped monitoring: {path_name}")

            self.observers.clear()
            self.logger.info("Stopped all file monitoring")

        except Exception as e:
            self.logger.error(f"Error stopping file monitoring: {e}")

    def _start_path_monitoring(self, path_name: str):
        """Start monitoring a specific path"""
        try:
            monitor_path = self.monitor_paths[path_name]

            # Create directory if it doesn't exist
            monitor_path.mkdir(parents=True, exist_ok=True)

            # Create event handler
            event_handler = RF4SFileHandler(
                path_name=path_name,
                file_patterns=self.file_patterns,
                callback=self._handle_file_event,
            )

            # Create and start observer
            observer = Observer()
            observer.schedule(event_handler, str(monitor_path), recursive=True)
            observer.start()

            self.observers[path_name] = observer
            self.logger.info(f"Started monitoring path: {monitor_path}")

        except Exception as e:
            self.logger.error(f"Error starting monitoring for {path_name}: {e}")

    def _handle_file_event(self, event: FileChangeEvent):
        """Handle file change events"""
        try:
            # Add metadata based on file type
            if event.file_type == "log":
                event.metadata = self._analyze_log_file(event.file_path)
            elif event.file_type == "screenshot":
                event.metadata = self._analyze_screenshot(event.file_path)
            elif event.file_type == "config":
                event.metadata = self._analyze_config_file(event.file_path)
            elif event.file_type == "session":
                event.metadata = self._analyze_session_file(event.file_path)

            # Notify callbacks
            self._notify_callbacks(event)

        except Exception as e:
            self.logger.error(f"Error handling file event: {e}")

    def _analyze_log_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze log file and extract metadata"""
        try:
            if not file_path.exists():
                return {}

            metadata = {
                "file_type": "log",
                "line_count": 0,
                "last_lines": [],
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
            }

            # Read last few lines and count log levels
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                metadata["line_count"] = len(lines)
                metadata["last_lines"] = [line.strip() for line in lines[-5:]]

                # Count log levels
                for line in lines:
                    line_lower = line.lower()
                    if "error" in line_lower:
                        metadata["error_count"] += 1
                    elif "warning" in line_lower or "warn" in line_lower:
                        metadata["warning_count"] += 1
                    elif "info" in line_lower:
                        metadata["info_count"] += 1

            return metadata

        except Exception as e:
            self.logger.error(f"Error analyzing log file {file_path}: {e}")
            return {}

    def _analyze_screenshot(self, file_path: Path) -> Dict[str, Any]:
        """Analyze screenshot file and extract metadata"""
        try:
            if not file_path.exists():
                return {}

            metadata = {
                "file_type": "screenshot",
                "format": file_path.suffix.lower(),
                "size_bytes": file_path.stat().st_size,
            }

            # Try to get image dimensions
            try:
                with Image.open(file_path) as img:
                    metadata.update(
                        {
                            "width": img.width,
                            "height": img.height,
                            "mode": img.mode,
                            "format": img.format,
                        }
                    )
            except Exception:
                pass

            return metadata

        except Exception as e:
            self.logger.error(f"Error analyzing screenshot {file_path}: {e}")
            return {}

    def _analyze_config_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze configuration file and extract metadata"""
        try:
            if not file_path.exists():
                return {}

            metadata = {
                "file_type": "config",
                "format": file_path.suffix.lower(),
                "size_bytes": file_path.stat().st_size,
                "key_count": 0,
            }

            # Try to parse and count keys
            try:
                if file_path.suffix.lower() in [".json"]:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            metadata["key_count"] = len(data)
                elif file_path.suffix.lower() in [".yaml", ".yml"]:
                    import yaml

                    with open(file_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if isinstance(data, dict):
                            metadata["key_count"] = len(data)
            except Exception:
                pass

            return metadata

        except Exception as e:
            self.logger.error(f"Error analyzing config file {file_path}: {e}")
            return {}

    def _analyze_session_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze session file and extract metadata"""
        try:
            if not file_path.exists():
                return {}

            metadata = {
                "file_type": "session",
                "format": file_path.suffix.lower(),
                "size_bytes": file_path.stat().st_size,
            }

            return metadata

        except Exception as e:
            self.logger.error(f"Error analyzing session file {file_path}: {e}")
            return {}

    def _notify_callbacks(self, event: FileChangeEvent):
        """Notify registered callbacks of file events"""
        try:
            for callback in self.event_callbacks.values():
                callback(event)
        except Exception as e:
            self.logger.error(f"Error notifying file event callbacks: {e}")

    def register_callback(self, name: str, callback: Callable):
        """Register callback for file events"""
        self.event_callbacks[name] = callback
        self.logger.info(f"Registered file event callback: {name}")

    def unregister_callback(self, name: str):
        """Unregister file event callback"""
        if name in self.event_callbacks:
            del self.event_callbacks[name]
            self.logger.info(f"Unregistered file event callback: {name}")

    def get_recent_files(
        self, file_type: str = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get list of recent files"""
        try:
            recent_files = []

            # Determine which paths to check
            paths_to_check = []
            if file_type:
                if file_type in self.monitor_paths:
                    paths_to_check = [self.monitor_paths[file_type]]
            else:
                paths_to_check = list(self.monitor_paths.values())

            # Collect files from all paths
            all_files = []
            for path in paths_to_check:
                if path.exists():
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            stat = file_path.stat()
                            all_files.append(
                                {
                                    "path": str(file_path),
                                    "name": file_path.name,
                                    "size": stat.st_size,
                                    "modified": datetime.fromtimestamp(stat.st_mtime),
                                    "created": datetime.fromtimestamp(stat.st_ctime),
                                    "type": self._get_file_type(file_path),
                                }
                            )

            # Sort by modification time and limit
            all_files.sort(key=lambda x: x["modified"], reverse=True)
            recent_files = all_files[:limit]

            return recent_files

        except Exception as e:
            self.logger.error(f"Error getting recent files: {e}")
            return []

    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension"""
        extension = file_path.suffix.lower()

        for file_type, extensions in self.file_patterns.items():
            if extension in extensions:
                return file_type

        return "other"

    def get_file_statistics(self) -> Dict[str, Any]:
        """Get file statistics for monitored paths"""
        try:
            stats = {"total_files": 0, "total_size": 0, "file_types": {}, "paths": {}}

            for path_name, path in self.monitor_paths.items():
                if not path.exists():
                    continue

                path_stats = {"files": 0, "size": 0, "types": {}}

                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        file_size = file_path.stat().st_size
                        file_type = self._get_file_type(file_path)

                        # Update totals
                        stats["total_files"] += 1
                        stats["total_size"] += file_size

                        # Update file type counts
                        if file_type not in stats["file_types"]:
                            stats["file_types"][file_type] = {"count": 0, "size": 0}
                        stats["file_types"][file_type]["count"] += 1
                        stats["file_types"][file_type]["size"] += file_size

                        # Update path stats
                        path_stats["files"] += 1
                        path_stats["size"] += file_size
                        if file_type not in path_stats["types"]:
                            path_stats["types"][file_type] = 0
                        path_stats["types"][file_type] += 1

                stats["paths"][path_name] = path_stats

            return stats

        except Exception as e:
            self.logger.error(f"Error getting file statistics: {e}")
            return {}

    def read_log_tail(self, log_name: str, lines: int = 50) -> List[str]:
        """Read the last N lines from a log file"""
        try:
            log_path = self.monitor_paths["logs"] / log_name
            if not log_path.exists():
                return []

            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]

        except Exception as e:
            self.logger.error(f"Error reading log tail for {log_name}: {e}")
            return []

    def search_logs(self, pattern: str, log_name: str = None) -> List[Dict[str, Any]]:
        """Search for pattern in log files"""
        try:
            results = []

            # Determine which log files to search
            if log_name:
                log_files = [self.monitor_paths["logs"] / log_name]
            else:
                log_files = list(self.monitor_paths["logs"].glob("*.log"))

            for log_file in log_files:
                if not log_file.exists():
                    continue

                try:
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern.lower() in line.lower():
                                results.append(
                                    {
                                        "file": log_file.name,
                                        "line_number": line_num,
                                        "line_content": line.strip(),
                                        "timestamp": datetime.fromtimestamp(
                                            log_file.stat().st_mtime
                                        ),
                                    }
                                )
                except Exception as e:
                    self.logger.error(f"Error searching in {log_file}: {e}")

            return results

        except Exception as e:
            self.logger.error(f"Error searching logs for pattern '{pattern}': {e}")
            return []

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_monitoring()
            self.event_callbacks.clear()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


class RF4SFileHandler(FileSystemEventHandler):
    """File system event handler for RF4S files"""

    def __init__(
        self, path_name: str, file_patterns: Dict[str, List[str]], callback: Callable
    ):
        self.path_name = path_name
        self.file_patterns = file_patterns
        self.callback = callback
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self._handle_event("created", event.src_path)

    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            self._handle_event("modified", event.src_path)

    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory:
            self._handle_event("deleted", event.src_path)

    def _handle_event(self, event_type: str, file_path: str):
        """Handle file system events"""
        try:
            path = Path(file_path)
            file_type = self._determine_file_type(path)

            # Get file info if file exists
            file_size = None
            file_hash = None
            if event_type != "deleted" and path.exists():
                try:
                    file_size = path.stat().st_size
                    if file_size < 1024 * 1024:  # Only hash files smaller than 1MB
                        with open(path, "rb") as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                except Exception:
                    pass

            # Create event object
            change_event = FileChangeEvent(
                event_type=event_type,
                file_path=path,
                file_type=file_type,
                timestamp=datetime.now(),
                file_size=file_size,
                file_hash=file_hash,
            )

            # Call callback
            self.callback(change_event)

        except Exception as e:
            self.logger.error(f"Error handling file event for {file_path}: {e}")

    def _determine_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension and path"""
        extension = file_path.suffix.lower()

        # Check against patterns
        for file_type, extensions in self.file_patterns.items():
            if extension in extensions:
                return file_type

        # Check based on path name
        if "log" in self.path_name:
            return "log"
        elif "screenshot" in self.path_name:
            return "screenshot"
        elif "config" in self.path_name:
            return "config"
        elif "session" in self.path_name:
            return "session"

        return "other"
