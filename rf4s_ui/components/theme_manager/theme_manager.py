#!/usr/bin/env python3
"""
RF4S UI - Theme Manager

This module manages themes and styling for the RF4S UI application.
Provides PyQt-Fluent-Widgets theme integration and custom styling capabilities.

Features:
- PyQt-Fluent-Widgets theme management
- Custom color schemes and styling
- Dark/Light mode switching
- Theme persistence and restoration
- Dynamic theme application
"""

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentStyleSheet, Theme, setTheme, setThemeColor
from qfluentwidgets.common.config import qconfig

from ...core.service_registry import ServiceRegistry


class ThemeManager(QObject):
    """
    Manages application themes and styling

    This manager handles theme switching, custom color schemes,
    and integration with PyQt-Fluent-Widgets theming system.
    """

    # Signals
    theme_changed = pyqtSignal(str)  # theme_name
    color_changed = pyqtSignal(str)  # color_name

    def __init__(self, service_registry: ServiceRegistry):
        super().__init__()

        self.service_registry = service_registry
        self.settings = service_registry.get("settings")

        # Theme configuration
        self.current_theme = "auto"
        self.current_color = "blue"
        self.custom_themes: Dict[str, Dict[str, Any]] = {}

        # Available themes
        self.available_themes = {
            "light": Theme.LIGHT,
            "dark": Theme.DARK,
            "auto": Theme.AUTO,
        }

        # Available accent colors
        self.available_colors = {
            "blue": "#0078d4",
            "purple": "#8764b8",
            "green": "#107c10",
            "orange": "#ff8c00",
            "red": "#d13438",
            "pink": "#e3008c",
            "teal": "#00bcf2",
            "lime": "#bad80a",
        }

        # RF4S specific color schemes
        self.rf4s_colors = {
            "fishing_blue": "#1e3a8a",
            "water_teal": "#0891b2",
            "fish_gold": "#f59e0b",
            "nature_green": "#059669",
            "sunset_orange": "#ea580c",
        }

        # Initialize theme system
        self._load_saved_theme()
        self._apply_current_theme()

    def _load_saved_theme(self):
        """Load saved theme preferences"""
        if self.settings:
            self.current_theme = self.settings.value("theme", "auto")
            self.current_color = self.settings.value("accent_color", "blue")

    def _apply_current_theme(self):
        """Apply the current theme configuration"""
        try:
            # Set main theme
            if self.current_theme in self.available_themes:
                theme = self.available_themes[self.current_theme]
                setTheme(theme)

            # Set accent color
            if self.current_color in self.available_colors:
                color = self.available_colors[self.current_color]
                setThemeColor(QColor(color))
            elif self.current_color in self.rf4s_colors:
                color = self.rf4s_colors[self.current_color]
                setThemeColor(QColor(color))

        except Exception as e:
            print(f"Error applying theme: {e}")

    def set_theme(self, theme_name: str):
        """Set the application theme"""
        if theme_name not in self.available_themes:
            print(f"Unknown theme: {theme_name}")
            return

        self.current_theme = theme_name

        # Apply theme
        theme = self.available_themes[theme_name]
        setTheme(theme)

        # Save preference
        if self.settings:
            self.settings.setValue("theme", theme_name)

        # Emit signal
        self.theme_changed.emit(theme_name)

    def set_accent_color(self, color_name: str):
        """Set the accent color"""
        color_value = None

        if color_name in self.available_colors:
            color_value = self.available_colors[color_name]
        elif color_name in self.rf4s_colors:
            color_value = self.rf4s_colors[color_name]
        else:
            print(f"Unknown color: {color_name}")
            return

        self.current_color = color_name

        # Apply color
        setThemeColor(QColor(color_value))

        # Save preference
        if self.settings:
            self.settings.setValue("accent_color", color_name)

        # Emit signal
        self.color_changed.emit(color_name)

    def get_current_theme(self) -> str:
        """Get current theme name"""
        return self.current_theme

    def get_current_color(self) -> str:
        """Get current accent color name"""
        return self.current_color

    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        return list(self.available_themes.keys())

    def get_available_colors(self) -> List[str]:
        """Get list of available colors"""
        return list(self.available_colors.keys()) + list(self.rf4s_colors.keys())

    def create_custom_theme(
        self, name: str, base_theme: str, custom_colors: Dict[str, str]
    ) -> bool:
        """Create a custom theme configuration"""
        if base_theme not in self.available_themes:
            return False

        custom_theme = {
            "base_theme": base_theme,
            "colors": custom_colors,
            "created_by": "user",
        }

        self.custom_themes[name] = custom_theme
        return True

    def apply_custom_theme(self, name: str) -> bool:
        """Apply a custom theme"""
        if name not in self.custom_themes:
            return False

        theme_config = self.custom_themes[name]

        # Apply base theme
        base_theme = theme_config["base_theme"]
        if base_theme in self.available_themes:
            setTheme(self.available_themes[base_theme])

        # Apply custom colors
        colors = theme_config.get("colors", {})
        if "accent" in colors:
            setThemeColor(QColor(colors["accent"]))

        self.current_theme = name
        self.theme_changed.emit(name)
        return True

    def get_theme_preview(self, theme_name: str) -> Dict[str, str]:
        """Get theme preview information"""
        if theme_name in self.available_themes:
            return {
                "name": theme_name,
                "type": "built-in",
                "description": f"Built-in {theme_name} theme",
            }
        elif theme_name in self.custom_themes:
            config = self.custom_themes[theme_name]
            return {
                "name": theme_name,
                "type": "custom",
                "base_theme": config["base_theme"],
                "description": f"Custom theme based on {config['base_theme']}",
            }
        else:
            return {}

    def export_theme_config(self) -> Dict[str, Any]:
        """Export current theme configuration"""
        return {
            "current_theme": self.current_theme,
            "current_color": self.current_color,
            "custom_themes": self.custom_themes,
        }

    def import_theme_config(self, config: Dict[str, Any]) -> bool:
        """Import theme configuration"""
        try:
            if "current_theme" in config:
                self.set_theme(config["current_theme"])

            if "current_color" in config:
                self.set_accent_color(config["current_color"])

            if "custom_themes" in config:
                self.custom_themes.update(config["custom_themes"])

            return True

        except Exception as e:
            print(f"Error importing theme config: {e}")
            return False

    def reset_to_defaults(self):
        """Reset theme to default settings"""
        self.set_theme("auto")
        self.set_accent_color("blue")
        self.custom_themes.clear()

    def get_rf4s_theme_suggestions(self) -> List[Dict[str, str]]:
        """Get RF4S-specific theme suggestions"""
        return [
            {
                "name": "Fishing Waters",
                "theme": "dark",
                "color": "water_teal",
                "description": "Dark theme with water-inspired colors",
            },
            {
                "name": "Golden Catch",
                "theme": "light",
                "color": "fish_gold",
                "description": "Light theme with golden accent",
            },
            {
                "name": "Deep Sea",
                "theme": "dark",
                "color": "fishing_blue",
                "description": "Deep blue theme for serious fishing",
            },
            {
                "name": "Nature's Edge",
                "theme": "light",
                "color": "nature_green",
                "description": "Natural green theme",
            },
            {
                "name": "Sunset Fishing",
                "theme": "auto",
                "color": "sunset_orange",
                "description": "Warm sunset colors",
            },
        ]

    def apply_rf4s_theme(self, suggestion_name: str) -> bool:
        """Apply an RF4S theme suggestion"""
        suggestions = self.get_rf4s_theme_suggestions()

        for suggestion in suggestions:
            if suggestion["name"] == suggestion_name:
                self.set_theme(suggestion["theme"])
                self.set_accent_color(suggestion["color"])
                return True

        return False

    def get_current_style_sheet(self) -> str:
        """Get current application stylesheet"""
        try:
            return FluentStyleSheet.FLUENT.content()
        except:
            return ""

    def cleanup(self):
        """Cleanup theme manager resources"""
        # Save current settings
        if self.settings:
            self.settings.setValue("theme", self.current_theme)
            self.settings.setValue("accent_color", self.current_color)


if __name__ == "__main__":
    # Test theme manager
    import sys

    from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget
    from qfluentwidgets import PushButton

    app = QApplication(sys.argv)

    # Create mock service registry
    from PyQt6.QtCore import QSettings

    from ...core.service_registry import ServiceRegistry

    service_registry = ServiceRegistry()
    settings = QSettings("RF4S", "RF4S-UI-Test")
    service_registry.register("settings", settings)

    # Create theme manager
    theme_manager = ThemeManager(service_registry)

    # Create test window
    window = QWidget()
    layout = QVBoxLayout(window)

    # Add theme switching buttons
    for theme_name in theme_manager.get_available_themes():
        btn = PushButton(f"Set {theme_name} theme")
        btn.clicked.connect(
            lambda checked, name=theme_name: theme_manager.set_theme(name)
        )
        layout.addWidget(btn)

    window.show()
    sys.exit(app.exec())
