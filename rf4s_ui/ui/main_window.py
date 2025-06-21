#!/usr/bin/env python3
"""
RF4S UI - Main Window

This module implements the main application window for the RF4S UI.
Provides the primary interface with multi-panel layout, toolbar, and menu system.

Features:
- Multi-panel layout management (2-4 panels)
- Integrated toolbar and menu system
- Real-time status monitoring
- Theme and layout customization
- Emergency controls and safety systems
"""

import sys
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QMenuBar,
                             QMessageBox, QSplitter, QStatusBar, QToolBar,
                             QVBoxLayout, QWidget)
from qfluentwidgets import (FluentIcon, InfoBar, InfoBarPosition, MessageBox,
                            NavigationInterface, NavigationItemPosition,
                            PushButton, StateToolTip, ToolButton)

from ..components.panel_manager import PanelManager
from ..components.settings_manager import SettingsManager
from ..components.theme_manager import ThemeManager
from ..core.service_registry import ServiceRegistry


class MainWindow(QMainWindow):
    """
    Main application window

    This is the primary window for the RF4S UI application, providing
    the main interface with multi-panel layout and integrated controls.
    """

    # Signals
    closing = pyqtSignal()
    emergency_stop_triggered = pyqtSignal()

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__()

        self.service_registry = service_registry

        # Get required services
        self.panel_manager = service_registry.get("panel_manager")
        self.theme_manager = service_registry.get("theme_manager")
        self.settings_manager = service_registry.get("settings_manager")

        # Window state
        self.is_emergency_mode = False
        self.status_tip: Optional[StateToolTip] = None

        # Initialize UI
        self._setup_window()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._setup_connections()
        self._restore_window_state()

        # Start status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # Update every 5 seconds

    def _setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("RF4S UI - Russian Fishing 4 Script Interface")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)

        # Set window icon (placeholder)
        # self.setWindowIcon(QIcon(":/icons/rf4s_icon.png"))

    def _setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        new_profile_action = QAction("&New Profile", self)
        new_profile_action.setShortcut(QKeySequence.StandardKey.New)
        new_profile_action.triggered.connect(self._new_profile)
        file_menu.addAction(new_profile_action)

        open_profile_action = QAction("&Open Profile", self)
        open_profile_action.setShortcut(QKeySequence.StandardKey.Open)
        open_profile_action.triggered.connect(self._open_profile)
        file_menu.addAction(open_profile_action)

        save_profile_action = QAction("&Save Profile", self)
        save_profile_action.setShortcut(QKeySequence.StandardKey.Save)
        save_profile_action.triggered.connect(self._save_profile)
        file_menu.addAction(save_profile_action)

        file_menu.addSeparator()

        import_action = QAction("&Import Settings", self)
        import_action.triggered.connect(self._import_settings)
        file_menu.addAction(import_action)

        export_action = QAction("&Export Settings", self)
        export_action.triggered.connect(self._export_settings)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu("&View")

        # Layout submenu
        layout_menu = view_menu.addMenu("&Layout")
        if self.panel_manager:
            for layout_name in self.panel_manager.get_available_layouts():
                action = QAction(layout_name.replace("-", " ").title(), self)
                action.triggered.connect(
                    lambda checked, name=layout_name: self._change_layout(name)
                )
                layout_menu.addAction(action)

        # Theme submenu
        theme_menu = view_menu.addMenu("&Theme")
        if self.theme_manager:
            for theme_name in self.theme_manager.get_available_themes():
                action = QAction(theme_name.title(), self)
                action.triggered.connect(
                    lambda checked, name=theme_name: self.theme_manager.set_theme(name)
                )
                theme_menu.addAction(action)

        view_menu.addSeparator()

        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence.StandardKey.FullScreen)
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")

        diagnostics_action = QAction("&Run Diagnostics", self)
        diagnostics_action.triggered.connect(self._run_diagnostics)
        tools_menu.addAction(diagnostics_action)

        backup_action = QAction("&Create Backup", self)
        backup_action.triggered.connect(self._create_backup)
        tools_menu.addAction(backup_action)

        settings_action = QAction("&Settings", self)
        settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
        settings_action.triggered.connect(self._open_settings)
        tools_menu.addAction(settings_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        help_action = QAction("&Help Documentation", self)
        help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

    def _setup_toolbar(self):
        """Setup the main toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # Start/Stop RF4S
        self.start_action = QAction("Start RF4S", self)
        self.start_action.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay)
        )
        self.start_action.triggered.connect(self._toggle_rf4s)
        toolbar.addAction(self.start_action)

        # Emergency Stop
        emergency_action = QAction("Emergency Stop", self)
        emergency_action.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_MediaStop)
        )
        emergency_action.triggered.connect(self._emergency_stop)
        toolbar.addAction(emergency_action)

        toolbar.addSeparator()

        # Layout switching
        layout_2_action = QAction("2 Panels", self)
        layout_2_action.triggered.connect(lambda: self._change_layout("2-panel"))
        toolbar.addAction(layout_2_action)

        layout_3_action = QAction("3 Panels", self)
        layout_3_action.triggered.connect(lambda: self._change_layout("3-panel"))
        toolbar.addAction(layout_3_action)

        layout_4_action = QAction("4 Panels", self)
        layout_4_action.triggered.connect(lambda: self._change_layout("4-panel"))
        toolbar.addAction(layout_4_action)

        toolbar.addSeparator()

        # Settings
        settings_action = QAction("Settings", self)
        settings_action.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        )
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)

        self.addToolBar(toolbar)

    def _setup_central_widget(self):
        """Setup the central widget with panel manager"""
        if self.panel_manager:
            central_widget = self.panel_manager.get_main_widget()
            self.setCentralWidget(central_widget)
        else:
            # Fallback widget
            fallback = QWidget()
            layout = QVBoxLayout(fallback)
            layout.addWidget(QWidget())  # Placeholder
            self.setCentralWidget(fallback)

    def _setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()

        # Status labels
        self.rf4s_status_label = QWidget()
        self.connection_status_label = QWidget()
        self.performance_label = QWidget()

        # Add to status bar
        self.status_bar.addWidget(self.rf4s_status_label)
        self.status_bar.addPermanentWidget(self.connection_status_label)
        self.status_bar.addPermanentWidget(self.performance_label)

        self.setStatusBar(self.status_bar)

        # Initial status
        self.status_bar.showMessage("RF4S UI Ready")

    def _setup_connections(self):
        """Setup signal connections"""
        # Panel manager connections
        if self.panel_manager:
            self.panel_manager.emergency_stop.connect(self._emergency_stop)

        # Theme manager connections
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self._on_theme_changed)

        # Settings manager connections
        if self.settings_manager:
            self.settings_manager.setting_changed.connect(self._on_setting_changed)

    def _restore_window_state(self):
        """Restore window state from settings"""
        if not self.settings_manager:
            return

        # Restore geometry
        geometry = self.settings_manager.get("ui/window_geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore window state
        state = self.settings_manager.get("ui/window_state")
        if state:
            self.restoreState(state)

    def _save_window_state(self):
        """Save window state to settings"""
        if not self.settings_manager:
            return

        self.settings_manager.set("ui/window_geometry", self.saveGeometry())
        self.settings_manager.set("ui/window_state", self.saveState())

    def _update_status(self):
        """Update status bar information"""
        # Update RF4S status
        rf4s_running = False  # TODO: Get actual status
        status_text = "RF4S: Running" if rf4s_running else "RF4S: Stopped"

        # Update connection status
        connection_text = "Connected" if rf4s_running else "Disconnected"

        # Update performance info
        # TODO: Get actual performance metrics
        performance_text = "CPU: 5% | Memory: 128MB"

        # Update status bar
        self.status_bar.showMessage(
            f"{status_text} | {connection_text} | {performance_text}"
        )

    def _toggle_rf4s(self):
        """Toggle RF4S start/stop"""
        # TODO: Implement actual RF4S control
        current_text = self.start_action.text()
        if "Start" in current_text:
            self.start_action.setText("Stop RF4S")
            self.start_action.setIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_MediaPause)
            )
            self._show_info("RF4S Started", "RF4S automation has been started")
        else:
            self.start_action.setText("Start RF4S")
            self.start_action.setIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay)
            )
            self._show_info("RF4S Stopped", "RF4S automation has been stopped")

    def _emergency_stop(self):
        """Handle emergency stop"""
        self.is_emergency_mode = True
        self.emergency_stop_triggered.emit()

        # Update UI
        self.start_action.setText("Start RF4S")
        self.start_action.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay)
        )

        # Show emergency notification
        self._show_warning(
            "Emergency Stop", "All RF4S operations have been stopped immediately"
        )

    def _change_layout(self, layout_name: str):
        """Change panel layout"""
        if self.panel_manager:
            success = self.panel_manager.set_layout(layout_name)
            if success:
                self._show_info("Layout Changed", f"Switched to {layout_name} layout")
            else:
                self._show_error(
                    "Layout Error", f"Failed to switch to {layout_name} layout"
                )

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _new_profile(self):
        """Create new profile"""
        # TODO: Implement profile creation dialog
        self._show_info("New Profile", "Profile creation not yet implemented")

    def _open_profile(self):
        """Open existing profile"""
        # TODO: Implement profile selection dialog
        self._show_info("Open Profile", "Profile loading not yet implemented")

    def _save_profile(self):
        """Save current profile"""
        if self.settings_manager:
            success = self.settings_manager.save_profile("current")
            if success:
                self._show_info("Profile Saved", "Current profile has been saved")
            else:
                self._show_error("Save Error", "Failed to save profile")

    def _import_settings(self):
        """Import settings from file"""
        # TODO: Implement file dialog and import
        self._show_info("Import Settings", "Settings import not yet implemented")

    def _export_settings(self):
        """Export settings to file"""
        # TODO: Implement file dialog and export
        self._show_info("Export Settings", "Settings export not yet implemented")

    def _run_diagnostics(self):
        """Run system diagnostics"""
        # TODO: Implement diagnostics
        self._show_info("Diagnostics", "System diagnostics not yet implemented")

    def _create_backup(self):
        """Create settings backup"""
        if self.settings_manager:
            success = self.settings_manager.create_backup()
            if success:
                self._show_info("Backup Created", "Settings backup has been created")
            else:
                self._show_error("Backup Error", "Failed to create backup")

    def _open_settings(self):
        """Open settings dialog"""
        # TODO: Implement settings dialog
        self._show_info("Settings", "Settings dialog not yet implemented")

    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About RF4S UI",
            "RF4S UI - Russian Fishing 4 Script Interface\n\n"
            "A modern, modular desktop application for managing\n"
            "RF4S automation with 350+ configurable features.\n\n"
            "Built with PyQt6 and PyQt-Fluent-Widgets",
        )

    def _show_help(self):
        """Show help documentation"""
        # TODO: Implement help system
        self._show_info("Help", "Help documentation not yet implemented")

    def _on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        self._show_info("Theme Changed", f"Theme changed to {theme_name}")

    def _on_setting_changed(self, key: str, value: Any):
        """Handle setting change"""
        # Update UI based on setting changes
        if key == "ui/show_toolbar":
            toolbar = self.findChild(QToolBar)
            if toolbar:
                toolbar.setVisible(value)
        elif key == "ui/show_statusbar":
            self.status_bar.setVisible(value)

    def _show_info(self, title: str, message: str):
        """Show info notification"""
        InfoBar.success(
            title=title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def _show_warning(self, title: str, message: str):
        """Show warning notification"""
        InfoBar.warning(
            title=title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self,
        )

    def _show_error(self, title: str, message: str):
        """Show error notification"""
        InfoBar.error(
            title=title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self,
        )

    def closeEvent(self, event):
        """Handle window close event"""
        # Save window state
        self._save_window_state()

        # Emit closing signal
        self.closing.emit()

        # Stop timers
        if hasattr(self, "status_timer"):
            self.status_timer.stop()

        # Accept the close event
        event.accept()

    def cleanup(self):
        """Cleanup main window resources"""
        if hasattr(self, "status_timer"):
            self.status_timer.stop()

        self._save_window_state()


if __name__ == "__main__":
    # Test main window
    app = QApplication(sys.argv)

    # Create mock service registry
    from ..components.panel_manager import PanelManager
    from ..components.settings_manager import SettingsManager
    from ..components.theme_manager import ThemeManager
    from ..core.service_registry import ServiceRegistry

    service_registry = ServiceRegistry()

    # Register mock services
    panel_manager = PanelManager(service_registry)
    theme_manager = ThemeManager(service_registry)
    settings_manager = SettingsManager(service_registry)

    service_registry.register("panel_manager", panel_manager)
    service_registry.register("theme_manager", theme_manager)
    service_registry.register("settings_manager", settings_manager)

    # Create and show main window
    window = MainWindow(service_registry)
    window.show()

    sys.exit(app.exec())
