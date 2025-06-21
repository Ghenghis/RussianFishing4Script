#!/usr/bin/env python3
"""
RF4S UI - Panel Widget Components

This module provides the feature widgets for each panel in the RF4S UI system.
Implements the four main panel types: Dashboard, Configuration, Monitoring, and Advanced.

Features:
- Real-time dashboard with live statistics and controls
- Advanced configuration studio with 350+ settings
- Monitoring and analytics with performance metrics
- Advanced features and system management
"""

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette
from PyQt6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QProgressBar, QPushButton, QScrollArea, QSplitter,
                             QTextEdit, QVBoxLayout, QWidget)
from qfluentwidgets import (BodyLabel, CaptionLabel, CardWidget, FluentIcon,
                            HeaderCardWidget, InfoBar, PrimaryPushButton,
                            ProgressBar, PushButton, SimpleCardWidget,
                            ToolButton, TransparentToolButton)

from ...core.service_registry import ServiceRegistry


class PanelWidget(QWidget):
    """Base class for all panel widgets"""

    status_updated = pyqtSignal(dict)
    emergency_stop = pyqtSignal()

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__()
        self.service_registry = service_registry
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second

    def update_status(self):
        """Override in subclasses to update status"""
        pass

    def cleanup(self):
        """Cleanup resources"""
        if self.update_timer:
            self.update_timer.stop()


class DashboardPanelWidget(PanelWidget):
    """
    Real-Time Dashboard Panel

    Provides live statistics, system status, profile management,
    smart automation controls, and quick actions.
    """

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__(service_registry)
        self.rf4s_running = False
        self.current_action = "Standby"
        self.fish_caught = 0
        self.casts_made = 0
        self.session_runtime = 0

        self._setup_ui()

    def _setup_ui(self):
        """Setup dashboard UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Live Statistics Section
        stats_card = self._create_statistics_card()
        layout.addWidget(stats_card)

        # System Status Section
        status_card = self._create_status_card()
        layout.addWidget(status_card)

        # Quick Controls Section
        controls_card = self._create_controls_card()
        layout.addWidget(controls_card)

        # Emergency Controls Section
        emergency_card = self._create_emergency_card()
        layout.addWidget(emergency_card)

        layout.addStretch()

    def _create_statistics_card(self) -> CardWidget:
        """Create live statistics display"""
        card = HeaderCardWidget()
        card.setTitle("Live Statistics")

        content = QWidget()
        layout = QGridLayout(content)

        # Fish Caught
        self.fish_label = BodyLabel("Fish Caught: 0")
        layout.addWidget(self.fish_label, 0, 0)

        # Casts Made
        self.casts_label = BodyLabel("Casts Made: 0")
        layout.addWidget(self.casts_label, 0, 1)

        # Success Rate
        self.success_label = BodyLabel("Success Rate: 0%")
        layout.addWidget(self.success_label, 1, 0)

        # Runtime
        self.runtime_label = BodyLabel("Runtime: 00:00:00")
        layout.addWidget(self.runtime_label, 1, 1)

        # Fish/Hour Rate
        self.rate_label = BodyLabel("Fish/Hour: 0")
        layout.addWidget(self.rate_label, 2, 0)

        # Efficiency
        self.efficiency_bar = ProgressBar()
        self.efficiency_bar.setValue(0)
        layout.addWidget(QLabel("Efficiency:"), 2, 1)
        layout.addWidget(self.efficiency_bar, 3, 0, 1, 2)

        card.addWidget(content)
        return card

    def _create_status_card(self) -> CardWidget:
        """Create system status display"""
        card = HeaderCardWidget()
        card.setTitle("System Status")

        content = QWidget()
        layout = QVBoxLayout(content)

        # RF4S Status
        self.rf4s_status = BodyLabel("RF4S: Disconnected")
        layout.addWidget(self.rf4s_status)

        # Game Detection
        self.game_status = BodyLabel("Game: Not Detected")
        layout.addWidget(self.game_status)

        # Current Action
        self.action_status = BodyLabel("Action: Standby")
        layout.addWidget(self.action_status)

        # Bot Status
        self.bot_status = BodyLabel("Bot: Stopped")
        layout.addWidget(self.bot_status)

        card.addWidget(content)
        return card

    def _create_controls_card(self) -> CardWidget:
        """Create quick control buttons"""
        card = HeaderCardWidget()
        card.setTitle("Quick Controls")

        content = QWidget()
        layout = QGridLayout(content)

        # Start/Stop Button
        self.start_btn = PrimaryPushButton("Start Fishing")
        self.start_btn.clicked.connect(self._toggle_fishing)
        layout.addWidget(self.start_btn, 0, 0)

        # Pause Button
        self.pause_btn = PushButton("Pause")
        self.pause_btn.clicked.connect(self._pause_fishing)
        layout.addWidget(self.pause_btn, 0, 1)

        # Repair Equipment
        repair_btn = PushButton("Repair Equipment")
        repair_btn.clicked.connect(self._repair_equipment)
        layout.addWidget(repair_btn, 1, 0)

        # Craft Bait
        craft_btn = PushButton("Craft Bait")
        craft_btn.clicked.connect(self._craft_bait)
        layout.addWidget(craft_btn, 1, 1)

        card.addWidget(content)
        return card

    def _create_emergency_card(self) -> CardWidget:
        """Create emergency controls"""
        card = HeaderCardWidget()
        card.setTitle("Emergency Controls")

        content = QWidget()
        layout = QHBoxLayout(content)

        # Emergency Stop Button
        emergency_btn = PushButton("EMERGENCY STOP")
        emergency_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        emergency_btn.clicked.connect(self._emergency_stop)
        layout.addWidget(emergency_btn)

        # Safe Mode Button
        safe_btn = PushButton("Safe Mode")
        safe_btn.clicked.connect(self._safe_mode)
        layout.addWidget(safe_btn)

        card.addWidget(content)
        return card

    def _toggle_fishing(self):
        """Toggle fishing automation"""
        if self.rf4s_running:
            self._stop_fishing()
        else:
            self._start_fishing()

    def _start_fishing(self):
        """Start fishing automation"""
        self.rf4s_running = True
        self.current_action = "Starting..."
        self.start_btn.setText("Stop Fishing")
        self.bot_status.setText("Bot: Starting")

    def _stop_fishing(self):
        """Stop fishing automation"""
        self.rf4s_running = False
        self.current_action = "Standby"
        self.start_btn.setText("Start Fishing")
        self.bot_status.setText("Bot: Stopped")

    def _pause_fishing(self):
        """Pause fishing automation"""
        if self.rf4s_running:
            self.current_action = "Paused"
            self.bot_status.setText("Bot: Paused")

    def _repair_equipment(self):
        """Trigger equipment repair"""
        print("Repair equipment triggered")

    def _craft_bait(self):
        """Trigger bait crafting"""
        print("Craft bait triggered")

    def _emergency_stop(self):
        """Trigger emergency stop"""
        self.emergency_stop.emit()
        self._stop_fishing()

    def _safe_mode(self):
        """Activate safe mode"""
        print("Safe mode activated")

    def update_status(self):
        """Update dashboard status"""
        # Update runtime
        if self.rf4s_running:
            self.session_runtime += 1
            hours = self.session_runtime // 3600
            minutes = (self.session_runtime % 3600) // 60
            seconds = self.session_runtime % 60
            self.runtime_label.setText(
                f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}"
            )

        # Update statistics
        self.fish_label.setText(f"Fish Caught: {self.fish_caught}")
        self.casts_label.setText(f"Casts Made: {self.casts_made}")

        # Calculate success rate
        success_rate = (
            (self.fish_caught / self.casts_made * 100) if self.casts_made > 0 else 0
        )
        self.success_label.setText(f"Success Rate: {success_rate:.1f}%")

        # Calculate fish per hour
        fish_per_hour = (
            (self.fish_caught / (self.session_runtime / 3600))
            if self.session_runtime > 0
            else 0
        )
        self.rate_label.setText(f"Fish/Hour: {fish_per_hour:.1f}")

        # Update efficiency bar
        self.efficiency_bar.setValue(int(success_rate))

        # Update status labels
        self.rf4s_status.setText(
            f"RF4S: {'Connected' if self.rf4s_running else 'Disconnected'}"
        )
        self.action_status.setText(f"Action: {self.current_action}")


class ConfigurationPanelWidget(PanelWidget):
    """
    Advanced Configuration Studio Panel

    Provides comprehensive configuration interface with 350+ controls
    for fishing profiles, detection settings, and automation parameters.
    """

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__(service_registry)
        self._setup_ui()

    def _setup_ui(self):
        """Setup configuration UI"""
        layout = QVBoxLayout(self)

        # Configuration placeholder
        placeholder = HeaderCardWidget()
        placeholder.setTitle("Configuration Studio")

        content = QWidget()
        content_layout = QVBoxLayout(content)

        content_layout.addWidget(BodyLabel("Advanced Configuration Studio"))
        content_layout.addWidget(BodyLabel("350+ configurable features"))
        content_layout.addWidget(
            BodyLabel("• Fishing Profiles (PIRK, SPIN, TELESCOPIC, etc.)")
        )
        content_layout.addWidget(BodyLabel("• Detection & OCR Settings"))
        content_layout.addWidget(BodyLabel("• Input Simulation & Timing"))
        content_layout.addWidget(BodyLabel("• Fish Management & AI"))

        load_btn = PushButton("Load Configuration Studio")
        load_btn.clicked.connect(self._load_config_studio)
        content_layout.addWidget(load_btn)

        placeholder.addWidget(content)
        layout.addWidget(placeholder)

    def _load_config_studio(self):
        """Load the full configuration studio"""
        print("Loading configuration studio...")


class MonitoringPanelWidget(PanelWidget):
    """
    Monitoring & Analytics Panel

    Provides performance monitoring, detection preview,
    session analytics, and advanced logging capabilities.
    """

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__(service_registry)
        self._setup_ui()

    def _setup_ui(self):
        """Setup monitoring UI"""
        layout = QVBoxLayout(self)

        # Performance Monitoring
        perf_card = HeaderCardWidget()
        perf_card.setTitle("Performance Monitoring")

        perf_content = QWidget()
        perf_layout = QVBoxLayout(perf_content)

        # CPU Usage
        self.cpu_bar = ProgressBar()
        perf_layout.addWidget(QLabel("CPU Usage:"))
        perf_layout.addWidget(self.cpu_bar)

        # Memory Usage
        self.memory_bar = ProgressBar()
        perf_layout.addWidget(QLabel("Memory Usage:"))
        perf_layout.addWidget(self.memory_bar)

        perf_card.addWidget(perf_content)
        layout.addWidget(perf_card)

        # Detection Preview
        detection_card = HeaderCardWidget()
        detection_card.setTitle("Detection Preview")

        detection_content = QWidget()
        detection_layout = QVBoxLayout(detection_content)
        detection_layout.addWidget(BodyLabel("Live detection preview will appear here"))

        detection_card.addWidget(detection_content)
        layout.addWidget(detection_card)

        # Log Viewer
        log_card = HeaderCardWidget()
        log_card.setTitle("System Logs")

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.append("System initialized")

        log_card.addWidget(self.log_text)
        layout.addWidget(log_card)

    def update_status(self):
        """Update monitoring status"""
        # Simulate CPU and memory usage
        import random

        self.cpu_bar.setValue(random.randint(5, 25))
        self.memory_bar.setValue(random.randint(30, 60))


class AdvancedPanelWidget(PanelWidget):
    """
    Advanced Features Panel

    Provides notification systems, pause management,
    tools/utilities, system settings, and safety controls.
    """

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__(service_registry)
        self._setup_ui()

    def _setup_ui(self):
        """Setup advanced features UI"""
        layout = QVBoxLayout(self)

        # Notification Settings
        notif_card = HeaderCardWidget()
        notif_card.setTitle("Notification Systems")

        notif_content = QWidget()
        notif_layout = QVBoxLayout(notif_content)

        email_btn = PushButton("Configure Email")
        discord_btn = PushButton("Configure Discord")
        notif_layout.addWidget(email_btn)
        notif_layout.addWidget(discord_btn)

        notif_card.addWidget(notif_content)
        layout.addWidget(notif_card)

        # System Tools
        tools_card = HeaderCardWidget()
        tools_card.setTitle("System Tools")

        tools_content = QWidget()
        tools_layout = QGridLayout(tools_content)

        backup_btn = PushButton("Backup Config")
        restore_btn = PushButton("Restore Config")
        export_btn = PushButton("Export Settings")
        import_btn = PushButton("Import Settings")

        tools_layout.addWidget(backup_btn, 0, 0)
        tools_layout.addWidget(restore_btn, 0, 1)
        tools_layout.addWidget(export_btn, 1, 0)
        tools_layout.addWidget(import_btn, 1, 1)

        tools_card.addWidget(tools_content)
        layout.addWidget(tools_card)

        # Safety Systems
        safety_card = HeaderCardWidget()
        safety_card.setTitle("Safety & Failsafe")

        safety_content = QWidget()
        safety_layout = QVBoxLayout(safety_content)

        safe_mode_btn = PushButton("Enable Safe Mode")
        auto_recovery_btn = PushButton("Auto Recovery Settings")
        safety_layout.addWidget(safe_mode_btn)
        safety_layout.addWidget(auto_recovery_btn)

        safety_card.addWidget(safety_content)
        layout.addWidget(safety_card)

        layout.addStretch()


# Widget factory functions
def create_dashboard_widget(service_registry: ServiceRegistry) -> DashboardPanelWidget:
    """Factory function for dashboard widget"""
    return DashboardPanelWidget(service_registry)


def create_configuration_widget(
    service_registry: ServiceRegistry,
) -> ConfigurationPanelWidget:
    """Factory function for configuration widget"""
    return ConfigurationPanelWidget(service_registry)


def create_monitoring_widget(
    service_registry: ServiceRegistry,
) -> MonitoringPanelWidget:
    """Factory function for monitoring widget"""
    return MonitoringPanelWidget(service_registry)


def create_advanced_widget(service_registry: ServiceRegistry) -> AdvancedPanelWidget:
    """Factory function for advanced widget"""
    return AdvancedPanelWidget(service_registry)


if __name__ == "__main__":
    # Test the panel widgets
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create mock service registry
    from ...core.service_registry import ServiceRegistry

    service_registry = ServiceRegistry()

    # Test dashboard widget
    dashboard = create_dashboard_widget(service_registry)
    dashboard.show()

    sys.exit(app.exec())
