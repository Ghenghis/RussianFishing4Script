#!/usr/bin/env python3
"""
RF4S UI Core Application

Main application logic for the RF4S PyQt-Fluent-Widgets UI.
Handles application lifecycle, component initialization, and coordination.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme, setThemeColor

from .component_loader import ComponentLoader
from .event_manager import EventManager
from .exceptions import RF4SUIException
from .service_registry import ServiceRegistry


class RF4SApplication:
    """
    Main application class for RF4S UI

    Manages application lifecycle, component loading, and core services.
    Provides centralized coordination for all UI components and features.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config"
        self.app: Optional[QApplication] = None
        self.main_window = None

        # Core services
        self.service_registry = ServiceRegistry()
        self.event_manager = EventManager()
        self.component_loader = ComponentLoader()

        # Application state
        self.is_initialized = False
        self.is_running = False

        # Setup logging
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup application logging"""
        logger = logging.getLogger(__name__)

        if not logger.handlers:
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)

        return logger

    def initialize(self) -> bool:
        """Initialize the application"""
        try:
            if self.is_initialized:
                self.logger.warning("Application already initialized")
                return True

            self.logger.info("Initializing RF4S UI Application")

            # Create QApplication if not exists
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
                self.app.setApplicationName("RF4S UI")
                self.app.setApplicationVersion("1.0.0")
                self.app.setOrganizationName("RF4S")
            else:
                self.app = QApplication.instance()

            # Setup theme
            self._setup_theme()

            # Register core services
            self._register_core_services()

            # Load components
            self._load_components()

            # Initialize main window
            self._initialize_main_window()

            # Setup event handlers
            self._setup_event_handlers()

            self.is_initialized = True
            self.logger.info("Application initialized successfully")

            # Publish initialization event
            self.event_manager.publish("app_initialized", source="application")

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False

    def _setup_theme(self):
        """Setup application theme"""
        try:
            # Set default theme to dark
            setTheme(Theme.DARK)

            # Set theme color (can be customized)
            setThemeColor("#0078d4")  # Microsoft Blue

            self.logger.debug("Theme setup completed")

        except Exception as e:
            self.logger.error(f"Failed to setup theme: {e}")

    def _register_core_services(self):
        """Register core services with the service registry"""
        try:
            # Register self
            self.service_registry.register_instance("application", self)

            # Register core services
            self.service_registry.register_instance(
                "service_registry", self.service_registry
            )
            self.service_registry.register_instance("event_manager", self.event_manager)
            self.service_registry.register_instance(
                "component_loader", self.component_loader
            )

            self.logger.debug("Core services registered")

        except Exception as e:
            self.logger.error(f"Failed to register core services: {e}")

    def _load_components(self):
        """Load all application components"""
        try:
            self.logger.info("Loading components...")

            # Load all components
            loaded_components = self.component_loader.load_all_components()

            self.logger.info(
                f"Loaded {len(loaded_components)} components: {list(loaded_components.keys())}"
            )

            # Publish component loaded event
            self.event_manager.publish(
                "components_loaded",
                data={"components": list(loaded_components.keys())},
                source="application",
            )

        except Exception as e:
            self.logger.error(f"Failed to load components: {e}")

    def _initialize_main_window(self):
        """Initialize the main application window"""
        try:
            # Try to get main window from service registry
            if self.service_registry.has_service("main_window"):
                self.main_window = self.service_registry.get_service("main_window")
            else:
                # Create a basic main window if none available
                from PyQt6.QtWidgets import QMainWindow

                self.main_window = QMainWindow()
                self.main_window.setWindowTitle("RF4S UI")
                self.main_window.resize(1200, 800)

                # Register it
                self.service_registry.register_instance("main_window", self.main_window)

            self.logger.debug("Main window initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize main window: {e}")

    def _setup_event_handlers(self):
        """Setup application-level event handlers"""
        try:
            # Subscribe to application events
            self.event_manager.subscribe("app_shutdown", self._handle_shutdown)
            self.event_manager.subscribe(
                "component_error", self._handle_component_error
            )

            self.logger.debug("Event handlers setup completed")

        except Exception as e:
            self.logger.error(f"Failed to setup event handlers: {e}")

    def _handle_shutdown(self, event):
        """Handle application shutdown event"""
        try:
            self.logger.info("Handling shutdown event")
            self.shutdown()
        except Exception as e:
            self.logger.error(f"Error handling shutdown: {e}")

    def _handle_component_error(self, event):
        """Handle component error events"""
        try:
            error_data = event.data
            component_name = error_data.get("component", "unknown")
            error_message = error_data.get("error", "Unknown error")

            self.logger.error(f"Component error in {component_name}: {error_message}")

            # Could implement error recovery logic here

        except Exception as e:
            self.logger.error(f"Error handling component error: {e}")

    def run(self) -> int:
        """Run the application"""
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return 1

            if not self.main_window:
                self.logger.error("No main window available")
                return 1

            self.logger.info("Starting RF4S UI Application")

            # Show main window
            self.main_window.show()

            # Publish app started event
            self.event_manager.publish("app_started", source="application")

            self.is_running = True

            # Start event loop
            return self.app.exec()

        except Exception as e:
            self.logger.error(f"Failed to run application: {e}")
            return 1

    def shutdown(self):
        """Shutdown the application"""
        try:
            if not self.is_running:
                return

            self.logger.info("Shutting down RF4S UI Application")

            # Publish shutdown event
            self.event_manager.publish("app_shutting_down", source="application")

            # Cleanup components
            self.component_loader.cleanup_all()

            # Shutdown services
            self.service_registry.shutdown_services()

            # Close main window
            if self.main_window:
                self.main_window.close()

            # Quit application
            if self.app:
                self.app.quit()

            self.is_running = False
            self.logger.info("Application shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def get_service(self, service_name: str):
        """Get a service from the registry"""
        return self.service_registry.get_service(service_name)

    def publish_event(self, event_name: str, data=None):
        """Publish an application event"""
        self.event_manager.publish(event_name, data, source="application")

    def get_component(self, component_name: str):
        """Get a loaded component"""
        return self.component_loader.get_component(component_name)

    def get_status(self) -> dict:
        """Get application status"""
        return {
            "initialized": self.is_initialized,
            "running": self.is_running,
            "components_loaded": len(self.component_loader.list_loaded_components()),
            "services_registered": len(self.service_registry.list_services()),
            "main_window_available": self.main_window is not None,
        }
