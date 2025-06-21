"""
RF4S Communication Bridges

This package provides non-invasive communication bridges to interface with RF4S
without modifying its source code.

Available bridges:
- ConfigurationBridge: Read/write RF4S configuration files
- ProcessBridge: Monitor and communicate with RF4S processes
- FileMonitorBridge: Monitor RF4S files for changes
"""

from .configuration_bridge import ConfigurationBridge
from .file_monitor_bridge import FileMonitorBridge
from .process_bridge import ProcessBridge

__all__ = ["ConfigurationBridge", "ProcessBridge", "FileMonitorBridge"]
