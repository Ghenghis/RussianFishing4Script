"""
RF4S UI - Panel Manager Component

This package provides the panel management system for the RF4S UI application,
enabling flexible multi-panel layouts with drag-and-drop customization.
"""

from .panel_layouts import PanelLayouts
from .panel_manager import PanelManager
from .panel_widgets import PanelWidget

__all__ = ["PanelManager", "PanelLayouts", "PanelWidget"]
