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
    from PyQt6.QtCore import QSettings, Qt, QTimer
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
from core.exceptions import RF4SUIException
# Import new modular architecture
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

            # Initialize Qt Application
            self._initialize_qt_app()

            # Run pre-launch diagnostics
            self._run_diagnostics()

            # Initialize core services
            self._initialize_services()

            # Create and show main window
            self._create_main_window()

            # Document the application startup
            self._document_startup()

            print("RF4S UI launched successfully with modular architecture!")
            print("Application ready for use.")

            # Run the application
            self.exit_code = self.qt_app.exec()

            return self.exit_code

        except Exception as e:
            self._handle_critical_error(e)
            return 1

    def _initialize_qt_app(self):
        """Initialize Qt application with proper settings"""
        self.qt_app = QApplication(sys.argv)

        # Set application properties
        self.qt_app.setApplicationName("RF4S UI")
        self.qt_app.setApplicationVersion("1.0.0")
        self.qt_app.setOrganizationName("RF4S")
        self.qt_app.setOrganizationDomain("rf4s.ui")

        # Enable high DPI scaling
        self.qt_app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        self.qt_app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        # Set default theme
        setTheme(Theme.AUTO)

    def _initialize_services(self):
        """Initialize all core services"""
        try:
            print("Initializing core services...")

            # Initialize QSettings for the service registry
            qt_settings = QSettings("RF4S", "RF4S-UI")
            self.service_registry.register("qt_settings", qt_settings)

            # Initialize Settings Manager
            settings_manager = SettingsManager(self.service_registry)
            self.service_registry.register("settings_manager", settings_manager)
            self.service_registry.register(
                "settings", qt_settings
            )  # Alias for compatibility

            # Initialize Theme Manager
            theme_manager = ThemeManager(self.service_registry)
            self.service_registry.register("theme_manager", theme_manager)

            # Initialize Panel Manager
            panel_manager = PanelManager(self.service_registry)
            self.service_registry.register("panel_manager", panel_manager)

            print("Core services initialized successfully")

        except Exception as e:
            print(f"ERROR: Failed to initialize services: {e}")
            raise

    def _create_main_window(self):
        """Create and show the main window"""
        try:
            print("Creating main window...")

            # Create main window
            self.main_window = MainWindow(self.service_registry)

            # Connect cleanup signal
            self.main_window.closing.connect(self._cleanup)

            # Show window
            self.main_window.show()

            print("Main window created and displayed")

        except Exception as e:
            print(f"ERROR: Failed to create main window: {e}")
            raise

    def _run_diagnostics(self):
        """Run comprehensive pre-launch diagnostics"""
        try:
            print("Running pre-launch diagnostics...")

            # Basic system checks
            print(f"Python version: {sys.version}")
            print(f"PyQt6 available: True")
            print(f"Project root: {project_root}")

            # Check required directories
            required_dirs = [
                project_root / "core",
                project_root / "components",
                project_root / "ui",
            ]

            for dir_path in required_dirs:
                if dir_path.exists():
                    print(f"✓ Directory exists: {dir_path.name}")
                else:
                    print(f"✗ Missing directory: {dir_path.name}")

            print("Diagnostics completed.")

        except Exception as e:
            print(f"Warning: Diagnostics failed: {e}")

    def _document_startup(self):
        """Document the application startup process"""
        try:
            startup_info = {
                "event": "rf4s_ui_startup",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "architecture": "PyQt6 + Fluent-Widgets + Modular",
                "services_registered": list(
                    self.service_registry.list_services().keys()
                ),
                "status": "successful",
            }

            print(
                f"Startup documented: {len(startup_info['services_registered'])} services registered"
            )

        except Exception as e:
            print(f"Warning: Startup documentation failed: {e}")

    def _handle_critical_error(self, error):
        """Handle critical application errors"""
        error_msg = f"Critical Error: {str(error)}"
        traceback_str = traceback.format_exc()

        print(f"\n{error_msg}")
        print(f"Traceback:\n{traceback_str}")

        # Try to show error dialog if Qt app is available
        if self.qt_app:
            try:
                QMessageBox.critical(
                    None,
                    "RF4S UI - Critical Error",
                    f"{error_msg}\n\nThe application will now exit.\n\nSee console for full traceback.",
                )
            except:
                pass  # If even the error dialog fails, just continue

        self.exit_code = 1

    def _cleanup(self):
        """Cleanup application resources"""
        try:
            print("Cleaning up application resources...")

            # Cleanup services
            settings_manager = self.service_registry.get("settings_manager")
            if settings_manager:
                settings_manager.cleanup()

            theme_manager = self.service_registry.get("theme_manager")
            if theme_manager:
                theme_manager.cleanup()

            panel_manager = self.service_registry.get("panel_manager")
            if panel_manager:
                panel_manager.cleanup()

            print("Cleanup completed")

        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")


def main():
    """Main entry point for RF4S UI"""
    try:
        # Create and run the launcher
        launcher = RF4SUILauncher()
        exit_code = launcher.run()

        print(f"RF4S UI exiting with code: {exit_code}")
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)

    except Exception as e:
        print(f"Fatal error during application startup: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
