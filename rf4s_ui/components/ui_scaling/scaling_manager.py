"""
Scaling Manager Component
Coordinates UI scaling, responsive layouts, and user preferences.
"""

from typing import Dict, List, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QSettings
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QResizeEvent
import logging

from .ui_scaler import UIScaler
from .responsive_layout import ResponsiveLayout


class ScalingManager(QObject):
    """Central manager for UI scaling and responsive behavior."""
    
    scaling_updated = pyqtSignal(float, str)  # scale_factor, layout_mode
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings()
        
        # Core components
        self.ui_scaler = UIScaler()
        self.responsive_layout = ResponsiveLayout()
        
        # Managed widgets
        self.managed_widgets: List[QWidget] = []
        self.resize_callbacks: List[Callable] = []
        
        # Auto-scaling settings
        self.auto_scale_enabled = True
        self.scale_presets = {
            "tiny": 0.75,
            "small": 0.9,
            "normal": 1.0,
            "large": 1.25,
            "huge": 1.5,
            "giant": 2.0,
        }
        
        self._setup_connections()
        self._load_preferences()
    
    def _setup_connections(self) -> None:
        """Setup signal connections between components."""
        try:
            # Connect UI scaler signals
            self.ui_scaler.scaling_changed.connect(self._on_scaling_changed)
            self.ui_scaler.font_changed.connect(self._on_font_changed)
            
            # Connect responsive layout signals
            self.responsive_layout.layout_changed.connect(self._on_layout_changed)
            
        except Exception as e:
            self.logger.error(f"Failed to setup connections: {e}")
    
    def _load_preferences(self) -> None:
        """Load user scaling preferences."""
        try:
            self.auto_scale_enabled = self.settings.value("scaling/auto_enabled", True, type=bool)
            
            # Load single-page mode preference
            single_page = self.settings.value("layout/single_page_mode", False, type=bool)
            self.responsive_layout.set_single_page_mode(single_page)
            
            # Load scroll preference
            scroll_enabled = self.settings.value("layout/scroll_enabled", True, type=bool)
            self.responsive_layout.set_scroll_enabled(scroll_enabled)
            
            self.logger.info(f"Loaded scaling preferences: auto={self.auto_scale_enabled}")
            
        except Exception as e:
            self.logger.error(f"Failed to load preferences: {e}")
    
    def _save_preferences(self) -> None:
        """Save current scaling preferences."""
        try:
            self.settings.setValue("scaling/auto_enabled", self.auto_scale_enabled)
            self.settings.setValue("layout/single_page_mode", self.responsive_layout.single_page_mode)
            self.settings.setValue("layout/scroll_enabled", self.responsive_layout.scroll_enabled)
            self.settings.sync()
        except Exception as e:
            self.logger.error(f"Failed to save preferences: {e}")
    
    def register_widget(self, widget: QWidget, auto_apply: bool = True) -> None:
        """Register a widget for automatic scaling management."""
        try:
            if widget not in self.managed_widgets:
                self.managed_widgets.append(widget)
                
                if auto_apply:
                    self.apply_scaling_to_widget(widget)
                
                # Install event filter for resize events
                widget.installEventFilter(self)
                
                self.logger.debug(f"Registered widget for scaling: {widget.__class__.__name__}")
                
        except Exception as e:
            self.logger.error(f"Failed to register widget: {e}")
    
    def unregister_widget(self, widget: QWidget) -> None:
        """Unregister a widget from scaling management."""
        try:
            if widget in self.managed_widgets:
                self.managed_widgets.remove(widget)
                widget.removeEventFilter(self)
                self.logger.debug(f"Unregistered widget from scaling: {widget.__class__.__name__}")
        except Exception as e:
            self.logger.error(f"Failed to unregister widget: {e}")
    
    def apply_scaling_to_widget(self, widget: QWidget) -> None:
        """Apply current scaling settings to a specific widget."""
        try:
            # Apply UI scaler settings
            self.ui_scaler.apply_to_widget(widget)
            
            # Apply responsive layout optimizations
            if widget.size().isValid():
                size = widget.size()
                self.responsive_layout.optimize_for_resolution(
                    widget, size.width(), size.height()
                )
                
        except Exception as e:
            self.logger.error(f"Failed to apply scaling to widget: {e}")
    
    def apply_scaling_to_all(self) -> None:
        """Apply current scaling to all managed widgets."""
        try:
            for widget in self.managed_widgets:
                if widget and not widget.isHidden():
                    self.apply_scaling_to_widget(widget)
            
            self.logger.info(f"Applied scaling to {len(self.managed_widgets)} widgets")
            
        except Exception as e:
            self.logger.error(f"Failed to apply scaling to all widgets: {e}")
    
    def set_scale_preset(self, preset_name: str) -> bool:
        """Set scaling using a predefined preset."""
        try:
            if preset_name in self.scale_presets:
                scale_factor = self.scale_presets[preset_name]
                self.ui_scaler.set_scale_factor(scale_factor)
                self.logger.info(f"Applied scale preset '{preset_name}': {scale_factor}x")
                return True
            else:
                self.logger.warning(f"Unknown scale preset: {preset_name}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to set scale preset: {e}")
            return False
    
    def set_custom_scale(self, scale_factor: float) -> None:
        """Set a custom scale factor."""
        try:
            self.ui_scaler.set_scale_factor(scale_factor)
            # Mark as manual scaling
            self.settings.setValue("ui/manual_scaling", "true")
        except Exception as e:
            self.logger.error(f"Failed to set custom scale: {e}")
    
    def set_font_settings(self, family: str, size: int) -> None:
        """Set font family and size."""
        try:
            self.ui_scaler.set_font_family(family)
            self.ui_scaler.set_font_size(size)
        except Exception as e:
            self.logger.error(f"Failed to set font settings: {e}")
    
    def toggle_single_page_mode(self) -> None:
        """Toggle single-page layout mode."""
        try:
            current = self.responsive_layout.single_page_mode
            self.responsive_layout.set_single_page_mode(not current)
            self._save_preferences()
            self.apply_scaling_to_all()
        except Exception as e:
            self.logger.error(f"Failed to toggle single-page mode: {e}")
    
    def toggle_scroll_mode(self) -> None:
        """Toggle scrolling enabled/disabled."""
        try:
            current = self.responsive_layout.scroll_enabled
            self.responsive_layout.set_scroll_enabled(not current)
            self._save_preferences()
            self.apply_scaling_to_all()
        except Exception as e:
            self.logger.error(f"Failed to toggle scroll mode: {e}")
    
    def handle_window_resize(self, width: int, height: int) -> None:
        """Handle main window resize events."""
        try:
            # Update responsive layout mode
            layout_changed = self.responsive_layout.update_layout_mode(width, height)
            
            if layout_changed or self.auto_scale_enabled:
                # Reapply scaling to all widgets
                self.apply_scaling_to_all()
                
                # Emit update signal
                self.scaling_updated.emit(
                    self.ui_scaler.current_scale,
                    self.responsive_layout.current_mode
                )
                
        except Exception as e:
            self.logger.error(f"Failed to handle window resize: {e}")
    
    def add_resize_callback(self, callback: Callable) -> None:
        """Add a callback to be called on resize events."""
        try:
            if callback not in self.resize_callbacks:
                self.resize_callbacks.append(callback)
        except Exception as e:
            self.logger.error(f"Failed to add resize callback: {e}")
    
    def get_scaling_info(self) -> Dict:
        """Get comprehensive scaling information."""
        try:
            return {
                "scale_factor": self.ui_scaler.current_scale,
                "layout_mode": self.responsive_layout.current_mode,
                "font_family": self.ui_scaler.font_family,
                "font_size": self.ui_scaler.current_font_size,
                "single_page_mode": self.responsive_layout.single_page_mode,
                "scroll_enabled": self.responsive_layout.scroll_enabled,
                "auto_scale_enabled": self.auto_scale_enabled,
                "managed_widgets": len(self.managed_widgets),
                "resolution_info": self.ui_scaler.get_resolution_info(),
            }
        except Exception as e:
            self.logger.error(f"Failed to get scaling info: {e}")
            return {}
    
    def reset_all_scaling(self) -> None:
        """Reset all scaling settings to defaults."""
        try:
            self.ui_scaler.reset_to_defaults()
            self.responsive_layout.set_single_page_mode(False)
            self.responsive_layout.set_scroll_enabled(True)
            self.auto_scale_enabled = True
            self._save_preferences()
            self.apply_scaling_to_all()
            self.logger.info("Reset all scaling settings to defaults")
        except Exception as e:
            self.logger.error(f"Failed to reset scaling: {e}")
    
    def _on_scaling_changed(self, scale_factor: float) -> None:
        """Handle scaling factor changes."""
        try:
            self.apply_scaling_to_all()
            self.scaling_updated.emit(scale_factor, self.responsive_layout.current_mode)
        except Exception as e:
            self.logger.error(f"Failed to handle scaling change: {e}")
    
    def _on_font_changed(self, font) -> None:
        """Handle font changes."""
        try:
            self.apply_scaling_to_all()
        except Exception as e:
            self.logger.error(f"Failed to handle font change: {e}")
    
    def _on_layout_changed(self, layout_mode: str) -> None:
        """Handle layout mode changes."""
        try:
            self.apply_scaling_to_all()
            
            # Execute resize callbacks
            for callback in self.resize_callbacks:
                try:
                    callback(layout_mode)
                except Exception as cb_error:
                    self.logger.error(f"Resize callback failed: {cb_error}")
                    
        except Exception as e:
            self.logger.error(f"Failed to handle layout change: {e}")
    
    def eventFilter(self, obj, event) -> bool:
        """Filter resize events for managed widgets."""
        try:
            if event.type() == event.Type.Resize and obj in self.managed_widgets:
                # Handle widget-specific resize
                resize_event = event
                if hasattr(resize_event, 'size'):
                    size = resize_event.size()
                    self.responsive_layout.optimize_for_resolution(
                        obj, size.width(), size.height()
                    )
        except Exception as e:
            self.logger.error(f"Failed to filter resize event: {e}")
        
        return super().eventFilter(obj, event)
