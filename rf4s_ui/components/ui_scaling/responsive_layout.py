"""
Responsive Layout Manager
Handles adaptive layouts for different screen sizes and orientations.
"""

from typing import Dict, List, Tuple, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QRect, QSize
from PyQt6.QtWidgets import (QWidget, QLayout, QVBoxLayout, QHBoxLayout, 
                            QGridLayout, QSplitter, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
import logging


class ResponsiveLayout(QObject):
    """Manages responsive layouts that adapt to screen size changes."""
    
    layout_changed = pyqtSignal(str)  # Emitted when layout mode changes
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Layout modes
        self.current_mode = "desktop"
        self.layout_modes = {
            "mobile": {"max_width": 768, "columns": 1, "spacing": 8},
            "tablet": {"max_width": 1024, "columns": 2, "spacing": 12},
            "desktop": {"max_width": 1920, "columns": 3, "spacing": 16},
            "large": {"max_width": 2560, "columns": 4, "spacing": 20},
            "ultra": {"max_width": 9999, "columns": 5, "spacing": 24},
        }
        
        # Layout preferences
        self.single_page_mode = False
        self.scroll_enabled = True
        self.adaptive_columns = True
        
        # Breakpoints for responsive behavior
        self.breakpoints = {
            "xs": 480,   # Extra small (phones)
            "sm": 768,   # Small (tablets)
            "md": 1024,  # Medium (small laptops)
            "lg": 1440,  # Large (desktops)
            "xl": 1920,  # Extra large (large monitors)
            "xxl": 2560, # Ultra large (4K monitors)
        }
    
    def detect_layout_mode(self, width: int, height: int) -> str:
        """Detect appropriate layout mode based on screen dimensions."""
        try:
            # Check each layout mode from smallest to largest
            for mode, config in self.layout_modes.items():
                if width <= config["max_width"]:
                    return mode
            
            # Default to largest mode if width exceeds all thresholds
            return "ultra"
            
        except Exception as e:
            self.logger.error(f"Failed to detect layout mode: {e}")
            return "desktop"
    
    def update_layout_mode(self, width: int, height: int) -> bool:
        """Update layout mode based on current dimensions."""
        try:
            new_mode = self.detect_layout_mode(width, height)
            if new_mode != self.current_mode:
                self.current_mode = new_mode
                self.layout_changed.emit(new_mode)
                self.logger.info(f"Layout mode changed to: {new_mode}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update layout mode: {e}")
            return False
    
    def get_layout_config(self, mode: Optional[str] = None) -> Dict:
        """Get configuration for specified layout mode."""
        mode = mode or self.current_mode
        return self.layout_modes.get(mode, self.layout_modes["desktop"])
    
    def create_responsive_grid(self, parent: QWidget, widgets: List[QWidget]) -> QGridLayout:
        """Create a responsive grid layout that adapts to screen size."""
        try:
            layout = QGridLayout(parent)
            config = self.get_layout_config()
            
            columns = config["columns"]
            spacing = config["spacing"]
            
            layout.setSpacing(spacing)
            layout.setContentsMargins(spacing, spacing, spacing, spacing)
            
            # Arrange widgets in grid
            for i, widget in enumerate(widgets):
                row = i // columns
                col = i % columns
                layout.addWidget(widget, row, col)
            
            # Make columns stretch equally
            for col in range(columns):
                layout.setColumnStretch(col, 1)
            
            return layout
            
        except Exception as e:
            self.logger.error(f"Failed to create responsive grid: {e}")
            return QGridLayout(parent)
    
    def create_adaptive_splitter(self, parent: QWidget, widgets: List[QWidget], 
                                orientation: Qt.Orientation = Qt.Orientation.Horizontal) -> QSplitter:
        """Create a splitter that adapts to screen size."""
        try:
            splitter = QSplitter(orientation, parent)
            
            for widget in widgets:
                splitter.addWidget(widget)
            
            # Set initial sizes based on layout mode
            config = self.get_layout_config()
            if config["columns"] <= 2:
                # For smaller screens, make panels more equal
                splitter.setSizes([1] * len(widgets))
            else:
                # For larger screens, allow more varied sizing
                sizes = []
                for i in range(len(widgets)):
                    if i == 0:  # First panel larger
                        sizes.append(2)
                    else:
                        sizes.append(1)
                splitter.setSizes(sizes)
            
            # Enable collapsible panels for mobile
            if self.current_mode in ["mobile", "tablet"]:
                splitter.setChildrenCollapsible(True)
            
            return splitter
            
        except Exception as e:
            self.logger.error(f"Failed to create adaptive splitter: {e}")
            return QSplitter(orientation, parent)
    
    def create_scrollable_container(self, parent: QWidget, content_widget: QWidget) -> QScrollArea:
        """Create a scrollable container for content."""
        try:
            scroll_area = QScrollArea(parent)
            scroll_area.setWidget(content_widget)
            scroll_area.setWidgetResizable(True)
            
            # Configure scrolling based on mode
            if self.single_page_mode and self.current_mode in ["desktop", "large", "ultra"]:
                # Disable scrolling for large screens in single-page mode
                scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            else:
                # Enable scrolling
                scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            return scroll_area
            
        except Exception as e:
            self.logger.error(f"Failed to create scrollable container: {e}")
            return QScrollArea(parent)
    
    def optimize_for_resolution(self, widget: QWidget, width: int, height: int) -> None:
        """Optimize widget layout for specific resolution."""
        try:
            # Determine breakpoint
            breakpoint = self.get_breakpoint(width)
            
            # Apply resolution-specific optimizations
            if breakpoint == "xs":  # Phone
                self._optimize_for_mobile(widget)
            elif breakpoint == "sm":  # Tablet
                self._optimize_for_tablet(widget)
            elif breakpoint in ["md", "lg"]:  # Desktop
                self._optimize_for_desktop(widget)
            elif breakpoint in ["xl", "xxl"]:  # Large monitors
                self._optimize_for_large_screen(widget)
                
        except Exception as e:
            self.logger.error(f"Failed to optimize for resolution: {e}")
    
    def get_breakpoint(self, width: int) -> str:
        """Get current breakpoint based on width."""
        for breakpoint, min_width in sorted(self.breakpoints.items(), 
                                          key=lambda x: x[1], reverse=True):
            if width >= min_width:
                return breakpoint
        return "xs"
    
    def _optimize_for_mobile(self, widget: QWidget) -> None:
        """Apply mobile-specific optimizations."""
        try:
            # Increase touch targets
            widget.setMinimumHeight(44)  # iOS/Android recommended minimum
            
            # Simplify layout
            if hasattr(widget, 'layout') and widget.layout():
                layout = widget.layout()
                layout.setSpacing(12)
                layout.setContentsMargins(16, 16, 16, 16)
                
        except Exception as e:
            self.logger.error(f"Failed to optimize for mobile: {e}")
    
    def _optimize_for_tablet(self, widget: QWidget) -> None:
        """Apply tablet-specific optimizations."""
        try:
            # Moderate spacing and margins
            if hasattr(widget, 'layout') and widget.layout():
                layout = widget.layout()
                layout.setSpacing(16)
                layout.setContentsMargins(20, 20, 20, 20)
                
        except Exception as e:
            self.logger.error(f"Failed to optimize for tablet: {e}")
    
    def _optimize_for_desktop(self, widget: QWidget) -> None:
        """Apply desktop-specific optimizations."""
        try:
            # Standard desktop spacing
            if hasattr(widget, 'layout') and widget.layout():
                layout = widget.layout()
                layout.setSpacing(12)
                layout.setContentsMargins(16, 16, 16, 16)
                
        except Exception as e:
            self.logger.error(f"Failed to optimize for desktop: {e}")
    
    def _optimize_for_large_screen(self, widget: QWidget) -> None:
        """Apply large screen optimizations."""
        try:
            # Increased spacing for better visual hierarchy
            if hasattr(widget, 'layout') and widget.layout():
                layout = widget.layout()
                layout.setSpacing(20)
                layout.setContentsMargins(24, 24, 24, 24)
                
        except Exception as e:
            self.logger.error(f"Failed to optimize for large screen: {e}")
    
    def set_single_page_mode(self, enabled: bool) -> None:
        """Enable or disable single-page mode."""
        try:
            if self.single_page_mode != enabled:
                self.single_page_mode = enabled
                self.logger.info(f"Single-page mode: {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Failed to set single-page mode: {e}")
    
    def set_scroll_enabled(self, enabled: bool) -> None:
        """Enable or disable scrolling."""
        try:
            if self.scroll_enabled != enabled:
                self.scroll_enabled = enabled
                self.logger.info(f"Scrolling: {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Failed to set scroll enabled: {e}")
    
    def get_optimal_panel_count(self, width: int) -> int:
        """Get optimal number of panels for given width."""
        try:
            config = self.get_layout_config(self.detect_layout_mode(width, 0))
            return config["columns"]
        except Exception as e:
            self.logger.error(f"Failed to get optimal panel count: {e}")
            return 2
