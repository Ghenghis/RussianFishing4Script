#!/usr/bin/env python3
"""
RF4S Main Application - Non-invasive PyQt-Fluent-Widgets UI
Core application class with multi-panel layout and bridge communication

This module implements the main application window with:
- Dynamic multi-panel layout (2, 3, or 4 panels)
- Non-invasive communication with RF4S core
- Automated event handling and error recovery
- Real-time status monitoring and updates
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QHBoxLayout, QMainWindow, QMenuBar, QSplitter,
                             QStatusBar, QToolBar, QVBoxLayout, QWidget)
from qfluentwidgets import (FluentIcon, InfoBar, InfoBarPosition,
                            NavigationInterface, NavigationItemPosition,
                            SplitTitleBar, Theme, TitleLabel, setTheme)

from ..widgets.configuration.fishing_modes import FishingModesWidget
# Widget imports
from ..widgets.configuration.general_settings import GeneralSettingsWidget
from ..widgets.controls.automation_panel import AutomationPanelWidget
from ..widgets.monitoring.detection_preview import DetectionPreviewWidget
from ..widgets.monitoring.status_dashboard import StatusDashboardWidget
from .bridge.config_bridge import RF4SConfigBridge
from .bridge.file_monitor import RF4SFileMonitor
from .bridge.process_bridge import RF4SProcessBridge
from .documentation_generator import DocumentationGenerator
from .memory_manager import MemoryManager
from .panel_manager import PanelManager
from .theme_manager import ThemeManager


class RF4SMainApplication(QMainWindow):
    """
    Main application window for RF4S UI with non-invasive integration

    Features:
    - Multi-panel layout management
    - Real-time RF4S communication
    - Automated error handling and recovery
    - Dynamic widget loading and management
    - Comprehensive logging and documentation
    """

    # Signals for cross-component communication
    rf4s_status_changed = pyqtSignal(dict)
    config_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str, str)  # error_type, error_message

    def __init__(self):
        super().__init__()

        # Core managers
        self.panel_manager = PanelManager()
        self.theme_manager = ThemeManager()
        self.memory_manager = MemoryManager()
        self.doc_generator = DocumentationGenerator()

        # Communication bridges (non-invasive)
        self.config_bridge = None
        self.process_bridge = None
        self.file_monitor = None

        # UI components
        self.navigation = None
        self.central_widget = None
        self.status_bar = None

        # Widget registry for dynamic loading
        self.widget_registry = {}
        self.active_widgets = {}

        # Monitoring and automation
        self.status_timer = QTimer()
        self.auto_save_timer = QTimer()

        # Initialize application
        self._initialize_application()

    def _initialize_application(self):
        """Initialize the complete application with error handling"""
        try:
            # Setup window properties
            self._setup_window()

            # Initialize communication bridges
            self._initialize_bridges()

            # Setup UI components
            self._setup_ui()

            # Register available widgets
            self._register_widgets()

            # Setup default layout
            self._setup_default_layout()

            # Initialize monitoring and automation
            self._setup_monitoring()

            # Connect signals
            self._connect_signals()

            # Document initialization
            self._document_initialization()

            # Show success message
            self._show_startup_success()

        except Exception as e:
            self._handle_initialization_error(e)

    def _setup_window(self):
        """Setup main window properties and styling"""
        self.setWindowTitle("RF4S UI - Russian Fishing 4 Script Interface")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)

        # Apply theme
        self.theme_manager.apply_theme(self)

        # Setup window icon
        icon_path = (
            Path(__file__).parent.parent / "resources" / "icons" / "rf4s_icon.ico"
        )
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _initialize_bridges(self):
        """Initialize communication bridges with RF4S (non-invasive)"""
        try:
            # Detect RF4S installation
            rf4s_path = self._detect_rf4s_installation()

            if rf4s_path:
                # Initialize configuration bridge
                config_path = rf4s_path / "config"
                self.config_bridge = RF4SConfigBridge(str(config_path))

                # Initialize process bridge
                self.process_bridge = RF4SProcessBridge()

                # Initialize file monitor
                self.file_monitor = RF4SFileMonitor(str(rf4s_path))

                # Test connections
                self._test_bridge_connections()

            else:
                self._handle_missing_rf4s()

        except Exception as e:
            self.error_occurred.emit("bridge_initialization", str(e))
            self._create_offline_mode()

    def _detect_rf4s_installation(self) -> Optional[Path]:
        """Detect RF4S installation directory"""
        # Check common installation paths
        possible_paths = [
            Path("C:/RF4S"),
            Path("C:/RussianFishing4Script"),
            Path.home() / "RF4S",
            Path.cwd().parent / "rf4s",  # Relative to current project
        ]

        for path in possible_paths:
            if path.exists() and (path / "rf4s").exists():
                self.memory_manager.store_setting("rf4s_path", str(path))
                return path

        return None

    def _setup_ui(self):
        """Setup the main UI components"""
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Setup navigation interface
        self._setup_navigation()

        # Setup panel management
        self._setup_panels()

        # Setup status bar
        self._setup_status_bar()

        # Setup menu bar
        self._setup_menu_bar()

    def _setup_navigation(self):
        """Setup the main navigation interface"""
        self.navigation = NavigationInterface(self)

        # Add navigation items
        self.navigation.addItem(
            routeKey="dashboard",
            icon=FluentIcon.HOME,
            text="Dashboard",
            onClick=lambda: self._show_widget("dashboard"),
        )

        self.navigation.addItem(
            routeKey="configuration",
            icon=FluentIcon.SETTING,
            text="Configuration",
            onClick=lambda: self._show_widget("configuration"),
        )

        self.navigation.addItem(
            routeKey="monitoring",
            icon=FluentIcon.SPEED_HIGH,
            text="Monitoring",
            onClick=lambda: self._show_widget("monitoring"),
        )

        self.navigation.addItem(
            routeKey="controls",
            icon=FluentIcon.PLAY,
            text="Controls",
            onClick=lambda: self._show_widget("controls"),
        )

        # Add separator
        self.navigation.addSeparator()

        # Add utility items
        self.navigation.addItem(
            routeKey="logs",
            icon=FluentIcon.DOCUMENT,
            text="Logs",
            onClick=lambda: self._show_widget("logs"),
        )

        self.navigation.addItem(
            routeKey="settings",
            icon=FluentIcon.SETTING,
            text="Settings",
            onClick=lambda: self._show_widget("settings"),
            position=NavigationItemPosition.BOTTOM,
        )

    def _setup_panels(self):
        """Setup the multi-panel layout system"""
        # Create main layout
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Add navigation to layout
        main_layout.addWidget(self.navigation)

        # Initialize panel manager with the remaining space
        panel_container = QWidget()
        main_layout.addWidget(panel_container, 1)  # Take remaining space

        # Setup panel manager
        self.panel_manager.setup_panels(panel_container)

    def _setup_status_bar(self):
        """Setup the status bar with real-time information"""
        self.status_bar = self.statusBar()

        # Add status indicators
        self.status_bar.showMessage("RF4S UI Ready")

        # Add permanent widgets for status
        # These will be updated by the monitoring system

    def _setup_menu_bar(self):
        """Setup the menu bar with actions"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_profile_action = QAction("New Profile", self)
        new_profile_action.triggered.connect(self._new_profile)
        file_menu.addAction(new_profile_action)

        load_profile_action = QAction("Load Profile", self)
        load_profile_action.triggered.connect(self._load_profile)
        file_menu.addAction(load_profile_action)

        save_profile_action = QAction("Save Profile", self)
        save_profile_action.triggered.connect(self._save_profile)
        file_menu.addAction(save_profile_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        layout_2_action = QAction("2-Panel Layout", self)
        layout_2_action.triggered.connect(
            lambda: self.panel_manager.set_layout_mode("2-panel")
        )
        view_menu.addAction(layout_2_action)

        layout_3_action = QAction("3-Panel Layout", self)
        layout_3_action.triggered.connect(
            lambda: self.panel_manager.set_layout_mode("3-panel")
        )
        view_menu.addAction(layout_3_action)

        layout_4_action = QAction("4-Panel Layout", self)
        layout_4_action.triggered.connect(
            lambda: self.panel_manager.set_layout_mode("4-panel")
        )
        view_menu.addAction(layout_4_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        diagnostics_action = QAction("Run Diagnostics", self)
        diagnostics_action.triggered.connect(self._run_diagnostics)
        tools_menu.addAction(diagnostics_action)

        repair_action = QAction("Auto Repair", self)
        repair_action.triggered.connect(self._run_auto_repair)
        tools_menu.addAction(repair_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _register_widgets(self):
        """Register all available widgets for dynamic loading"""
        # Configuration widgets
        self.widget_registry["general_settings"] = GeneralSettingsWidget
        self.widget_registry["fishing_modes"] = FishingModesWidget

        # Monitoring widgets
        self.widget_registry["status_dashboard"] = StatusDashboardWidget
        self.widget_registry["detection_preview"] = DetectionPreviewWidget

        # Control widgets
        self.widget_registry["automation_panel"] = AutomationPanelWidget

        # Document widget registration
        self.doc_generator.document_widget_registry(self.widget_registry)

    def _setup_default_layout(self):
        """Setup the default 3-panel layout"""
        try:
            # Set 3-panel layout as default
            self.panel_manager.set_layout_mode("3-panel")

            # Load default widgets into panels
            self._load_widget_to_panel("status_dashboard", "panel_1")
            self._load_widget_to_panel("general_settings", "panel_2")
            self._load_widget_to_panel("automation_panel", "panel_3")

        except Exception as e:
            self.error_occurred.emit("layout_setup", str(e))

    def _setup_monitoring(self):
        """Setup monitoring timers and automation"""
        # Status monitoring timer
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # Update every 5 seconds

        # Auto-save timer
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(300000)  # Auto-save every 5 minutes

    def _connect_signals(self):
        """Connect all signal handlers"""
        # Error handling
        self.error_occurred.connect(self._handle_error)

        # Status updates
        self.rf4s_status_changed.connect(self._on_status_changed)

        # Configuration updates
        self.config_updated.connect(self._on_config_updated)

    def _load_widget_to_panel(self, widget_name: str, panel_id: str):
        """Load a widget into a specific panel"""
        try:
            if widget_name in self.widget_registry:
                widget_class = self.widget_registry[widget_name]

                # Create widget instance with bridges
                widget_kwargs = {}
                if (
                    hasattr(widget_class, "requires_config_bridge")
                    and self.config_bridge
                ):
                    widget_kwargs["config_bridge"] = self.config_bridge
                if (
                    hasattr(widget_class, "requires_process_bridge")
                    and self.process_bridge
                ):
                    widget_kwargs["process_bridge"] = self.process_bridge
                if hasattr(widget_class, "requires_file_monitor") and self.file_monitor:
                    widget_kwargs["file_monitor"] = self.file_monitor

                widget = widget_class(**widget_kwargs)

                # Add to panel
                self.panel_manager.add_widget_to_panel(panel_id, widget)

                # Track active widget
                self.active_widgets[f"{panel_id}_{widget_name}"] = widget

                # Document widget loading
                self.doc_generator.document_widget_load(widget_name, panel_id)

        except Exception as e:
            self.error_occurred.emit(
                "widget_loading", f"Failed to load {widget_name}: {str(e)}"
            )

    def _show_widget(self, widget_category: str):
        """Show widgets for a specific category"""
        # This will be implemented to show category-specific widgets
        # For now, just update the navigation
        self.navigation.setCurrentItem(widget_category)

    def _update_status(self):
        """Update application status from RF4S bridges"""
        try:
            status_info = {}

            # Get process status
            if self.process_bridge:
                process_status = self.process_bridge.get_status()
                status_info.update(process_status)

            # Get file monitor status
            if self.file_monitor:
                file_status = self.file_monitor.get_status()
                status_info.update(file_status)

            # Emit status update
            self.rf4s_status_changed.emit(status_info)

        except Exception as e:
            self.error_occurred.emit("status_update", str(e))

    def _auto_save(self):
        """Perform automatic save operations"""
        try:
            # Save current layout
            self.panel_manager.save_layout_state()

            # Save application state
            self.memory_manager.save_application_state(
                {
                    "layout_mode": self.panel_manager.layout_mode,
                    "active_widgets": list(self.active_widgets.keys()),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            self.error_occurred.emit("auto_save", str(e))

    def _handle_error(self, error_type: str, error_message: str):
        """Handle application errors with user notification and logging"""
        # Log error
        error_details = {
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
        }

        self.memory_manager.store_error(error_details)
        self.doc_generator.document_error(error_details)

        # Show user notification
        InfoBar.error(
            title=f"Error: {error_type}",
            content=error_message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self,
        )

    def _on_status_changed(self, status: dict):
        """Handle RF4S status changes"""
        # Update status bar
        if "process_status" in status:
            self.status_bar.showMessage(f"RF4S: {status['process_status']}")

    def _on_config_updated(self, config: dict):
        """Handle configuration updates"""
        # Store configuration update
        self.memory_manager.store_configuration(config)

        # Document configuration change
        self.doc_generator.document_config_change(config)

    def _document_initialization(self):
        """Document successful application initialization"""
        init_info = {
            "timestamp": datetime.now().isoformat(),
            "layout_mode": self.panel_manager.layout_mode,
            "bridges_active": {
                "config": self.config_bridge is not None,
                "process": self.process_bridge is not None,
                "file_monitor": self.file_monitor is not None,
            },
            "widgets_registered": len(self.widget_registry),
        }

        self.memory_manager.store_event(
            {"type": "application_initialized", "details": init_info}
        )

        self.doc_generator.document_initialization(init_info)

    def _show_startup_success(self):
        """Show startup success notification"""
        InfoBar.success(
            title="RF4S UI Ready",
            content="Application initialized successfully",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    # Placeholder methods for menu actions
    def _new_profile(self):
        pass

    def _load_profile(self):
        pass

    def _save_profile(self):
        pass

    def _run_diagnostics(self):
        pass

    def _run_auto_repair(self):
        pass

    def _show_about(self):
        pass

    def _test_bridge_connections(self):
        pass

    def _handle_missing_rf4s(self):
        pass

    def _create_offline_mode(self):
        pass

    def _handle_initialization_error(self, error):
        pass
