#!/usr/bin/env python3
"""
RF4S UI - Panel Manager

This module manages the multi-panel layout system for the RF4S UI application.
Provides flexible 2-4 panel configurations with drag-and-drop customization.

Features:
- Dynamic panel layout switching (2-4 panels)
- Drag-and-drop panel customization
- Panel content management and routing
- Real-time status monitoring across panels
- Emergency control integration
"""

from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QSplitter, QStackedWidget,
                             QTabWidget, QVBoxLayout, QWidget)
from qfluentwidgets import (CardWidget, FluentIcon, HeaderCardWidget, InfoBar,
                            InfoBarPosition, PushButton, SimpleCardWidget,
                            ToolButton)

from ...core.event_manager import EventManager
from ...core.service_registry import ServiceRegistry
from .panel_layouts import PanelLayouts
from .panel_widgets import (AdvancedPanelWidget, ConfigurationPanelWidget,
                            DashboardPanelWidget, MonitoringPanelWidget)


class PanelManager(QObject):
    """
    Manages the multi-panel layout system

    This manager handles the creation, arrangement, and coordination of
    multiple panels in the RF4S UI application. It supports flexible
    layouts from 2-4 panels with customizable content.
    """

    # Signals
    layout_changed = pyqtSignal(str)  # layout_type
    panel_content_changed = pyqtSignal(str, str)  # panel_id, content_type
    emergency_triggered = pyqtSignal()
    status_updated = pyqtSignal(dict)  # status_data

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__()

        self.service_registry = service_registry
        self.event_manager = service_registry.get("event_manager")

        # Layout management
        self.current_layout = "2-panel"
        self.panel_layouts = PanelLayouts()
        self.central_widget: Optional[QWidget] = None
        self.main_splitter: Optional[QSplitter] = None

        # Panel widgets
        self.panels: Dict[str, QWidget] = {}
        self.panel_contents: Dict[str, str] = {}

        # Feature widgets
        self.dashboard_widget: Optional[DashboardPanelWidget] = None
        self.config_widget: Optional[ConfigurationPanelWidget] = None
        self.monitoring_widget: Optional[MonitoringPanelWidget] = None
        self.advanced_widget: Optional[AdvancedPanelWidget] = None

        # Status tracking
        self.status_data: Dict[str, Any] = {}
        self.emergency_conditions: List[str] = []

        # Initialize components
        self._create_central_widget()
        self._create_feature_widgets()
        self._setup_default_layout()
        self._connect_signals()

    def _create_central_widget(self):
        """Create the central widget for panel management"""
        self.central_widget = QWidget()
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        layout.addWidget(self.main_splitter)

    def _create_feature_widgets(self):
        """Create feature panel widgets"""
        try:
            self.dashboard_widget = DashboardPanelWidget(self.service_registry)
            self.config_widget = ConfigurationPanelWidget(self.service_registry)
            self.monitoring_widget = MonitoringPanelWidget(self.service_registry)
            self.advanced_widget = AdvancedPanelWidget(self.service_registry)

        except Exception as e:
            print(f"Error creating feature widgets: {e}")
            # Create placeholder widgets if feature widgets fail
            self._create_placeholder_widgets()

    def _create_placeholder_widgets(self):
        """Create placeholder widgets for development"""
        self.dashboard_widget = self._create_placeholder("Dashboard Panel")
        self.config_widget = self._create_placeholder("Configuration Panel")
        self.monitoring_widget = self._create_placeholder("Monitoring Panel")
        self.advanced_widget = self._create_placeholder("Advanced Panel")

    def _create_placeholder(self, title: str) -> QWidget:
        """Create a placeholder widget"""
        widget = HeaderCardWidget()
        widget.setTitle(title)
        widget.setMinimumSize(300, 200)

        layout = QVBoxLayout()
        layout.addWidget(PushButton(f"Load {title}"))
        widget.addWidget(QWidget())
        widget.widget().setLayout(layout)

        return widget

    def _setup_default_layout(self):
        """Setup the default 2-panel layout"""
        self.set_layout("2-panel")

    def _connect_signals(self):
        """Connect internal signals"""
        if self.dashboard_widget and hasattr(self.dashboard_widget, "emergency_stop"):
            self.dashboard_widget.emergency_stop.connect(self.emergency_triggered.emit)

    def get_central_widget(self) -> QWidget:
        """Get the central widget for the main window"""
        return self.central_widget

    def get_dashboard_widget(self) -> QWidget:
        """Get dashboard widget for navigation"""
        return self.dashboard_widget or self._create_placeholder("Dashboard")

    def get_config_widget(self) -> QWidget:
        """Get configuration widget for navigation"""
        return self.config_widget or self._create_placeholder("Configuration")

    def get_monitoring_widget(self) -> QWidget:
        """Get monitoring widget for navigation"""
        return self.monitoring_widget or self._create_placeholder("Monitoring")

    def get_advanced_widget(self) -> QWidget:
        """Get advanced widget for navigation"""
        return self.advanced_widget or self._create_placeholder("Advanced")

    def set_layout(self, layout_type: str):
        """Set the panel layout type"""
        if layout_type not in self.panel_layouts.get_available_layouts():
            print(f"Unknown layout type: {layout_type}")
            return

        # Clear current layout
        self._clear_layout()

        # Apply new layout
        layout_config = self.panel_layouts.get_layout_config(layout_type)
        self._apply_layout(layout_config)

        self.current_layout = layout_type
        self.layout_changed.emit(layout_type)

    def _clear_layout(self):
        """Clear the current panel layout"""
        if self.main_splitter:
            # Remove all widgets from splitter
            while self.main_splitter.count() > 0:
                child = self.main_splitter.widget(0)
                if child:
                    child.setParent(None)

    def _apply_layout(self, layout_config: Dict[str, Any]):
        """Apply a specific layout configuration"""
        panel_count = layout_config.get("panel_count", 2)
        orientation = layout_config.get("orientation", "horizontal")
        panel_assignments = layout_config.get("default_assignments", [])

        # Set splitter orientation
        if orientation == "vertical":
            self.main_splitter.setOrientation(Qt.Orientation.Vertical)
        else:
            self.main_splitter.setOrientation(Qt.Orientation.Horizontal)

        # Create panels based on configuration
        for i in range(panel_count):
            panel_widget = self._create_panel_container(f"panel_{i}")
            self.main_splitter.addWidget(panel_widget)

            # Assign default content if specified
            if i < len(panel_assignments):
                content_type = panel_assignments[i]
                self._set_panel_content(f"panel_{i}", content_type)

        # Set equal sizes for all panels
        sizes = [100] * panel_count
        self.main_splitter.setSizes(sizes)

    def _create_panel_container(self, panel_id: str) -> QWidget:
        """Create a container for a panel"""
        container = QFrame()
        container.setFrameStyle(QFrame.Shape.StyledPanel)
        container.setMinimumSize(300, 200)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create panel header with controls
        header = self._create_panel_header(panel_id)
        layout.addWidget(header)

        # Create content area
        content_area = QStackedWidget()
        content_area.setObjectName(f"{panel_id}_content")
        layout.addWidget(content_area)

        # Store panel reference
        self.panels[panel_id] = container

        return container

    def _create_panel_header(self, panel_id: str) -> QWidget:
        """Create header controls for a panel"""
        header = QWidget()
        header.setMaximumHeight(40)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        # Panel selector dropdown (placeholder for now)
        selector_btn = PushButton("Select Content")
        selector_btn.clicked.connect(lambda: self._show_content_selector(panel_id))
        layout.addWidget(selector_btn)

        layout.addStretch()

        # Panel controls
        maximize_btn = ToolButton(FluentIcon.FULL_SCREEN)
        maximize_btn.clicked.connect(lambda: self._maximize_panel(panel_id))
        layout.addWidget(maximize_btn)

        return header

    def _set_panel_content(self, panel_id: str, content_type: str):
        """Set content for a specific panel"""
        if panel_id not in self.panels:
            return

        # Get content area
        container = self.panels[panel_id]
        content_area = container.findChild(QStackedWidget, f"{panel_id}_content")
        if not content_area:
            return

        # Clear existing content
        while content_area.count() > 0:
            widget = content_area.widget(0)
            content_area.removeWidget(widget)

        # Add new content based on type
        content_widget = self._get_content_widget(content_type)
        if content_widget:
            content_area.addWidget(content_widget)
            content_area.setCurrentWidget(content_widget)

        # Update tracking
        self.panel_contents[panel_id] = content_type
        self.panel_content_changed.emit(panel_id, content_type)

    def _get_content_widget(self, content_type: str) -> Optional[QWidget]:
        """Get widget for specific content type"""
        content_map = {
            "dashboard": self.dashboard_widget,
            "configuration": self.config_widget,
            "monitoring": self.monitoring_widget,
            "advanced": self.advanced_widget,
        }

        return content_map.get(content_type)

    def _show_content_selector(self, panel_id: str):
        """Show content selector for panel"""
        # Placeholder for content selection dialog
        print(f"Show content selector for {panel_id}")

    def _maximize_panel(self, panel_id: str):
        """Maximize/restore a panel"""
        # Placeholder for panel maximization
        print(f"Maximize panel {panel_id}")

    def update_status(self):
        """Update status information across all panels"""
        try:
            # Collect status from all feature widgets
            status_data = {
                "timestamp": QTimer().remainingTime(),
                "panels_active": len(self.panels),
                "current_layout": self.current_layout,
                "emergency_mode": len(self.emergency_conditions) > 0,
            }

            # Update individual panel status
            for panel_id, content_type in self.panel_contents.items():
                widget = self._get_content_widget(content_type)
                if widget and hasattr(widget, "update_status"):
                    widget.update_status()

            self.status_data = status_data
            self.status_updated.emit(status_data)

        except Exception as e:
            print(f"Status update error: {e}")

    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of current status"""
        return {
            "rf4s_running": False,  # Placeholder
            "current_action": "Standby",  # Placeholder
            "panels_count": len(self.panels),
            "layout": self.current_layout,
            "emergency_active": len(self.emergency_conditions) > 0,
        }

    def check_emergency_conditions(self) -> Dict[str, Any]:
        """Check for emergency conditions"""
        # Placeholder emergency checking logic
        emergency_detected = len(self.emergency_conditions) > 0

        return {
            "emergency_detected": emergency_detected,
            "conditions": self.emergency_conditions,
            "reason": self.emergency_conditions[0]
            if self.emergency_conditions
            else None,
        }

    def add_emergency_condition(self, condition: str):
        """Add an emergency condition"""
        if condition not in self.emergency_conditions:
            self.emergency_conditions.append(condition)

    def clear_emergency_conditions(self):
        """Clear all emergency conditions"""
        self.emergency_conditions.clear()

    def get_available_layouts(self) -> List[str]:
        """Get list of available panel layouts"""
        return self.panel_layouts.get_available_layouts()

    def get_current_layout(self) -> str:
        """Get current layout type"""
        return self.current_layout

    def cleanup(self):
        """Cleanup panel manager resources"""
        try:
            # Cleanup feature widgets
            for widget in [
                self.dashboard_widget,
                self.config_widget,
                self.monitoring_widget,
                self.advanced_widget,
            ]:
                if widget and hasattr(widget, "cleanup"):
                    widget.cleanup()

            # Clear panels
            self.panels.clear()
            self.panel_contents.clear()

        except Exception as e:
            print(f"Cleanup error: {e}")


if __name__ == "__main__":
    # For testing purposes
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create mock service registry
    service_registry = ServiceRegistry()

    # Create panel manager
    panel_manager = PanelManager(service_registry)

    # Show central widget
    widget = panel_manager.get_central_widget()
    widget.show()

    sys.exit(app.exec())
