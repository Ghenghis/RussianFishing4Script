#!/usr/bin/env python3
"""
RF4S PyQt-Fluent-Widgets UI - Main Application Entry Point
Non-invasive UI integration for Russian Fishing 4 Script

This application provides a modern desktop interface for RF4S without
modifying the original source code. It communicates with RF4S through
file monitoring, configuration bridges, and process communication.

Uses the new modular architecture for improved maintainability.

Author: RF4S UI Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from qfluentwidgets import FluentIcon, Theme, setTheme
except ImportError as e:
    print(f"ERROR: Missing required dependencies. Please install requirements:")
    print(f"pip install -r requirements.txt")
    print(f"Import error: {e}")
    sys.exit(1)

from components.panel_manager import PanelManager
from components.settings_manager import SettingsManager
from components.theme_manager import ThemeManager
# Import new modular architecture
from core.application import Application
from core.exceptions import RF4SUIException
from core.service_registry import ServiceRegistry
from ui.main_window import MainWindow


class RF4SUILauncher:
    """
    Main launcher for RF4S UI with automated diagnostics and error handling
    Uses the new modular architecture for component management.
    """

    def __init__(self):
        self.qt_app = None
        self.service_registry = ServiceRegistry()
        self.main_window = None
        self.exit_code = 0

    def run(self):
        """
        Launch the RF4S UI application with full error handling and diagnostics
        """
        try:
            print("Starting RF4S UI with modular architecture...")

            # Run pre-launch diagnostics
            self._run_diagnostics()

            # Initialize the modular application
            if not self.rf4s_app.initialize():
                print("ERROR: Failed to initialize RF4S application")
                return 1

            # Document the application startup
            self._document_startup()

            print("RF4S UI launched successfully with modular architecture!")
            print("Application ready for use.")

            # Run the application
            self.exit_code = self.rf4s_app.run()

            return self.exit_code

        except Exception as e:
            self._handle_critical_error(e)
            return 1

    def _run_diagnostics(self):
        """Run comprehensive pre-launch diagnostics"""
        try:
            print("Running pre-launch diagnostics...")

            # Check if diagnostics component is available
            if self.rf4s_app.service_registry.has_service("auto_diagnostics"):
                diagnostics = self.rf4s_app.get_service("auto_diagnostics")

                # System diagnostics
                system_info = diagnostics.check_system_requirements()
                if not system_info.get("meets_requirements", True):
                    print("WARNING: System may not meet all requirements")
                    for issue in system_info.get("issues", []):
                        print(f"  - {issue}")

                # Dependency diagnostics
                deps_info = diagnostics.check_dependencies()
                if not deps_info.get("all_available", True):
                    print("WARNING: Some dependencies may be missing")
                    for missing in deps_info.get("missing", []):
                        print(f"  - Missing: {missing}")

                # RF4S integration diagnostics
                rf4s_info = diagnostics.check_rf4s_integration()
                if not rf4s_info.get("rf4s_available", False):
                    print("INFO: RF4S not currently running (will monitor for startup)")
            else:
                print(
                    "INFO: Diagnostics component not yet loaded, will run basic checks"
                )
                # Basic Python and PyQt checks
                print(f"Python version: {sys.version}")
                print(f"PyQt6 available: True")

            print("Diagnostics completed.")

        except Exception as e:
            print(f"Warning: Diagnostics failed: {e}")

    def _document_startup(self):
        """Document the application startup process"""
        try:
            # Check if documentation generator is available
            if self.rf4s_app.service_registry.has_service("doc_generator"):
                doc_generator = self.rf4s_app.get_service("doc_generator")

                startup_doc = {
                    "event": "rf4s_ui_startup",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "architecture": "PyQt6 + Fluent-Widgets + Modular",
                    "components_loaded": self.rf4s_app.component_loader.list_loaded_components(),
                    "services_registered": list(
                        self.rf4s_app.service_registry.list_services().keys()
                    ),
                    "status": "successful",
                }

                doc_generator.document_event(startup_doc)
            else:
                print("INFO: Documentation generator not yet loaded")

        except Exception as e:
            print(f"Warning: Startup documentation failed: {e}")

    def _handle_critical_error(self, error):
        """Handle critical application errors with detailed reporting"""
        try:
            error_details = {
                "type": "critical_error",
                "timestamp": datetime.now().isoformat(),
                "error": str(error),
                "traceback": traceback.format_exc(),
                "application_status": self.rf4s_app.get_status()
                if hasattr(self.rf4s_app, "get_status")
                else {},
            }

            # Store error in memory if available
            if self.rf4s_app.service_registry.has_service("memory_manager"):
                memory_manager = self.rf4s_app.get_service("memory_manager")
                memory_manager.store_error(error_details)

            # Generate error documentation if available
            if self.rf4s_app.service_registry.has_service("doc_generator"):
                doc_generator = self.rf4s_app.get_service("doc_generator")
                doc_generator.document_error(error_details)

            # Show user-friendly error dialog
            try:
                from PyQt6.QtWidgets import QApplication, QMessageBox

                if QApplication.instance():
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Icon.Critical)
                    msg.setWindowTitle("RF4S UI Critical Error")
                    msg.setText("A critical error occurred in RF4S UI")
                    msg.setDetailedText(
                        f"Error: {error}\n\nPlease check the logs for more details."
                    )
                    msg.exec()
            except:
                pass  # GUI not available

            print(f"CRITICAL ERROR: {error}")
            print(f"Full traceback:\n{traceback.format_exc()}")

            # Attempt graceful shutdown
            try:
                self.rf4s_app.shutdown()
            except:
                pass

        except Exception as meta_error:
            print(f"Meta-error in error handling: {meta_error}")
            print(f"Original error: {error}")


def main():
    """Main entry point with comprehensive error handling"""
    try:
        launcher = RF4SUILauncher()
        return launcher.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
    except RF4SUIException as e:
        print(f"RF4S UI Error: {e}")
        return 1
    except Exception as e:
        print(f"Fatal error during application startup: {e}")
        traceback.print_exc()
        return 1
    finally:
        # Ensure cleanup
        try:
            if "launcher" in locals() and hasattr(launcher, "rf4s_app"):
                launcher.rf4s_app.shutdown()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
