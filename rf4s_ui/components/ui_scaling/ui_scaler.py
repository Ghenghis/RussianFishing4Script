"""
UI Scaler Component
Handles dynamic UI scaling, font sizing, and resolution adaptation.
"""

from typing import Dict, Tuple, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal, QSettings, QTimer
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QFont, QScreen
import logging


class UIScaler(QObject):
    """Manages UI scaling across different resolutions and user preferences."""
    
    scaling_changed = pyqtSignal(float)  # Emitted when scaling factor changes
    font_changed = pyqtSignal(QFont)     # Emitted when font settings change
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings()
        
        # Scaling configuration
        self.base_dpi = 96.0
        self.current_scale = 1.0
        self.min_scale = 0.5
        self.max_scale = 3.0
        
        # Font configuration
        self.base_font_size = 10
        self.current_font_size = self.base_font_size
        self.font_family = "Segoe UI"
        
        # Resolution presets
        self.resolution_presets = {
            "phone": (360, 640, 0.8),      # Small phone
            "tablet": (768, 1024, 1.0),    # Tablet
            "hd": (1366, 768, 1.0),        # HD laptop
            "fhd": (1920, 1080, 1.2),      # Full HD
            "2k": (2560, 1440, 1.4),       # 2K monitor
            "4k": (3840, 2160, 1.8),       # 4K monitor
        }
        
        self._load_settings()
        self._setup_auto_detection()
    
    def _load_settings(self) -> None:
        """Load scaling settings from persistent storage."""
        try:
            self.current_scale = float(self.settings.value("ui/scale_factor", 1.0))
            self.current_font_size = int(self.settings.value("ui/font_size", self.base_font_size))
            self.font_family = self.settings.value("ui/font_family", "Segoe UI")
            
            # Clamp values to valid ranges
            self.current_scale = max(self.min_scale, min(self.max_scale, self.current_scale))
            self.current_font_size = max(8, min(72, self.current_font_size))
            
            self.logger.info(f"Loaded UI scaling: {self.current_scale}x, font: {self.font_family} {self.current_font_size}pt")
        except Exception as e:
            self.logger.warning(f"Failed to load UI settings: {e}")
    
    def _save_settings(self) -> None:
        """Save current scaling settings."""
        try:
            self.settings.setValue("ui/scale_factor", self.current_scale)
            self.settings.setValue("ui/font_size", self.current_font_size)
            self.settings.setValue("ui/font_family", self.font_family)
            self.settings.sync()
        except Exception as e:
            self.logger.error(f"Failed to save UI settings: {e}")
    
    def _setup_auto_detection(self) -> None:
        """Setup automatic resolution detection and scaling."""
        try:
            app = QApplication.instance()
            if app:
                primary_screen = app.primaryScreen()
                if primary_screen:
                    self._detect_optimal_scaling(primary_screen)
        except Exception as e:
            self.logger.error(f"Failed to setup auto-detection: {e}")
    
    def _detect_optimal_scaling(self, screen: QScreen) -> None:
        """Detect optimal scaling based on screen properties."""
        try:
            geometry = screen.geometry()
            dpi = screen.logicalDotsPerInch()
            width, height = geometry.width(), geometry.height()
            
            # Calculate DPI-based scaling
            dpi_scale = dpi / self.base_dpi
            
            # Find matching resolution preset
            resolution_scale = 1.0
            for preset_name, (preset_w, preset_h, preset_scale) in self.resolution_presets.items():
                if abs(width - preset_w) < 100 and abs(height - preset_h) < 100:
                    resolution_scale = preset_scale
                    self.logger.info(f"Detected {preset_name} resolution: {width}x{height}")
                    break
            
            # Combine DPI and resolution scaling
            suggested_scale = min(dpi_scale, resolution_scale)
            
            # Only auto-apply if user hasn't manually set scaling
            if self.settings.value("ui/manual_scaling", False) != "true":
                self.set_scale_factor(suggested_scale)
                
        except Exception as e:
            self.logger.error(f"Failed to detect optimal scaling: {e}")
    
    def set_scale_factor(self, scale: float) -> None:
        """Set the UI scale factor."""
        try:
            scale = max(self.min_scale, min(self.max_scale, scale))
            if abs(scale - self.current_scale) > 0.01:  # Avoid unnecessary updates
                self.current_scale = scale
                self._save_settings()
                self.scaling_changed.emit(scale)
                self.logger.info(f"UI scale factor changed to: {scale}x")
        except Exception as e:
            self.logger.error(f"Failed to set scale factor: {e}")
    
    def set_font_size(self, size: int) -> None:
        """Set the base font size."""
        try:
            size = max(8, min(72, size))
            if size != self.current_font_size:
                self.current_font_size = size
                self._save_settings()
                self._emit_font_changed()
                self.logger.info(f"Font size changed to: {size}pt")
        except Exception as e:
            self.logger.error(f"Failed to set font size: {e}")
    
    def set_font_family(self, family: str) -> None:
        """Set the font family."""
        try:
            if family and family != self.font_family:
                self.font_family = family
                self._save_settings()
                self._emit_font_changed()
                self.logger.info(f"Font family changed to: {family}")
        except Exception as e:
            self.logger.error(f"Failed to set font family: {e}")
    
    def _emit_font_changed(self) -> None:
        """Emit font changed signal with current font."""
        try:
            font = QFont(self.font_family, int(self.current_font_size * self.current_scale))
            self.font_changed.emit(font)
        except Exception as e:
            self.logger.error(f"Failed to emit font changed signal: {e}")
    
    def get_scaled_size(self, base_size: int) -> int:
        """Get scaled size based on current scale factor."""
        return int(base_size * self.current_scale)
    
    def get_scaled_font(self, base_size: Optional[int] = None) -> QFont:
        """Get scaled font with current settings."""
        size = base_size or self.current_font_size
        scaled_size = int(size * self.current_scale)
        return QFont(self.font_family, scaled_size)
    
    def apply_to_widget(self, widget: QWidget) -> None:
        """Apply current scaling to a widget."""
        try:
            if widget:
                # Apply font scaling
                font = self.get_scaled_font()
                widget.setFont(font)
                
                # Apply size scaling if widget has size hints
                if hasattr(widget, 'sizeHint'):
                    hint = widget.sizeHint()
                    if hint.isValid():
                        scaled_hint = hint * self.current_scale
                        widget.setMinimumSize(scaled_hint)
                        
        except Exception as e:
            self.logger.error(f"Failed to apply scaling to widget: {e}")
    
    def get_resolution_info(self) -> Dict[str, Any]:
        """Get current resolution and scaling information."""
        try:
            app = QApplication.instance()
            if app and app.primaryScreen():
                screen = app.primaryScreen()
                geometry = screen.geometry()
                return {
                    "width": geometry.width(),
                    "height": geometry.height(),
                    "dpi": screen.logicalDotsPerInch(),
                    "scale_factor": self.current_scale,
                    "font_size": self.current_font_size,
                    "font_family": self.font_family,
                }
        except Exception as e:
            self.logger.error(f"Failed to get resolution info: {e}")
        
        return {}
    
    def reset_to_defaults(self) -> None:
        """Reset scaling to default values."""
        try:
            self.current_scale = 1.0
            self.current_font_size = self.base_font_size
            self.font_family = "Segoe UI"
            self._save_settings()
            self.scaling_changed.emit(self.current_scale)
            self._emit_font_changed()
            self.logger.info("UI scaling reset to defaults")
        except Exception as e:
            self.logger.error(f"Failed to reset scaling: {e}")
