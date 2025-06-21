#!/usr/bin/env python3
"""
RF4S UI - Panel Layout Configurations

This module defines the available panel layout configurations for the RF4S UI.
Supports flexible 2-4 panel arrangements with customizable orientations.

Features:
- Pre-defined layout configurations
- Dynamic layout switching
- Panel assignment management
- Responsive layout adaptation
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class LayoutConfig:
    """Configuration for a panel layout"""

    name: str
    panel_count: int
    orientation: str  # "horizontal", "vertical", "grid"
    default_assignments: List[str]
    description: str
    splitter_sizes: List[int]
    min_panel_size: Tuple[int, int]  # (width, height)


class PanelLayouts:
    """
    Manages panel layout configurations

    This class provides predefined layout configurations and utilities
    for managing multi-panel arrangements in the RF4S UI.
    """

    def __init__(self):
        self.layouts = self._create_layout_definitions()

    def _create_layout_definitions(self) -> Dict[str, LayoutConfig]:
        """Create predefined layout configurations"""
        return {
            "2-panel": LayoutConfig(
                name="2-Panel Horizontal",
                panel_count=2,
                orientation="horizontal",
                default_assignments=["dashboard", "configuration"],
                description="Two panels side by side - ideal for monitoring and configuration",
                splitter_sizes=[50, 50],
                min_panel_size=(400, 300),
            ),
            "2-panel-vertical": LayoutConfig(
                name="2-Panel Vertical",
                panel_count=2,
                orientation="vertical",
                default_assignments=["dashboard", "monitoring"],
                description="Two panels stacked vertically - great for dashboard and logs",
                splitter_sizes=[60, 40],
                min_panel_size=(600, 250),
            ),
            "3-panel": LayoutConfig(
                name="3-Panel Layout",
                panel_count=3,
                orientation="horizontal",
                default_assignments=["dashboard", "configuration", "monitoring"],
                description="Three panels for comprehensive workflow",
                splitter_sizes=[35, 35, 30],
                min_panel_size=(300, 300),
            ),
            "3-panel-mixed": LayoutConfig(
                name="3-Panel Mixed",
                panel_count=3,
                orientation="mixed",  # Special handling required
                default_assignments=["dashboard", "configuration", "monitoring"],
                description="Dashboard on left, config and monitoring stacked on right",
                splitter_sizes=[50, 25, 25],
                min_panel_size=(300, 250),
            ),
            "4-panel": LayoutConfig(
                name="4-Panel Grid",
                panel_count=4,
                orientation="grid",
                default_assignments=[
                    "dashboard",
                    "configuration",
                    "monitoring",
                    "advanced",
                ],
                description="Four panels in a 2x2 grid - maximum workspace",
                splitter_sizes=[25, 25, 25, 25],
                min_panel_size=(300, 200),
            ),
            "4-panel-horizontal": LayoutConfig(
                name="4-Panel Horizontal",
                panel_count=4,
                orientation="horizontal",
                default_assignments=[
                    "dashboard",
                    "configuration",
                    "monitoring",
                    "advanced",
                ],
                description="Four panels in a row - ultra-wide setup",
                splitter_sizes=[25, 25, 25, 25],
                min_panel_size=(250, 400),
            ),
        }

    def get_available_layouts(self) -> List[str]:
        """Get list of available layout names"""
        return list(self.layouts.keys())

    def get_layout_config(self, layout_name: str) -> Dict[str, Any]:
        """Get configuration for a specific layout"""
        if layout_name not in self.layouts:
            # Return default 2-panel layout
            layout_name = "2-panel"

        config = self.layouts[layout_name]
        return {
            "name": config.name,
            "panel_count": config.panel_count,
            "orientation": config.orientation,
            "default_assignments": config.default_assignments,
            "description": config.description,
            "splitter_sizes": config.splitter_sizes,
            "min_panel_size": config.min_panel_size,
        }

    def get_layout_description(self, layout_name: str) -> str:
        """Get description for a layout"""
        config = self.layouts.get(layout_name)
        return config.description if config else "Unknown layout"

    def get_recommended_layout(self, screen_width: int, screen_height: int) -> str:
        """Get recommended layout based on screen size"""
        aspect_ratio = screen_width / screen_height

        # Ultra-wide screens (21:9 or wider)
        if aspect_ratio >= 2.3:
            return "4-panel-horizontal"

        # Wide screens (16:9, 16:10)
        elif aspect_ratio >= 1.6:
            if screen_width >= 1920:
                return "3-panel"
            else:
                return "2-panel"

        # Square-ish screens (4:3, 5:4)
        elif aspect_ratio >= 1.2:
            return "2-panel-vertical"

        # Portrait or very square screens
        else:
            return "2-panel-vertical"

    def validate_layout_config(self, layout_name: str) -> bool:
        """Validate that a layout configuration is valid"""
        if layout_name not in self.layouts:
            return False

        config = self.layouts[layout_name]

        # Check that assignments match panel count
        if len(config.default_assignments) > config.panel_count:
            return False

        # Check that splitter sizes are reasonable
        if len(config.splitter_sizes) != config.panel_count:
            return False

        # Check that sizes sum to approximately 100 (allowing for rounding)
        total_size = sum(config.splitter_sizes)
        if abs(total_size - 100) > 5:
            return False

        return True

    def get_content_types(self) -> List[str]:
        """Get available content types for panels"""
        return [
            "dashboard",
            "configuration",
            "monitoring",
            "advanced",
            "logs",
            "status",
            "controls",
            "analytics",
            "settings",
            "help",
        ]

    def get_content_description(self, content_type: str) -> str:
        """Get description for content type"""
        descriptions = {
            "dashboard": "Real-time status and quick controls",
            "configuration": "Fishing profiles and settings",
            "monitoring": "Performance metrics and analytics",
            "advanced": "System settings and tools",
            "logs": "Application logs and debugging",
            "status": "System status and health monitoring",
            "controls": "Manual controls and overrides",
            "analytics": "Session analytics and reporting",
            "settings": "Application preferences",
            "help": "Documentation and tutorials",
        }
        return descriptions.get(content_type, "Unknown content type")

    def get_optimal_assignment(self, layout_name: str, panel_index: int) -> str:
        """Get optimal content assignment for a panel position"""
        config = self.layouts.get(layout_name)
        if not config:
            return "dashboard"

        if panel_index < len(config.default_assignments):
            return config.default_assignments[panel_index]

        # Fallback assignments for additional panels
        fallback_order = ["advanced", "logs", "status", "controls"]
        fallback_index = panel_index - len(config.default_assignments)

        if fallback_index < len(fallback_order):
            return fallback_order[fallback_index]

        return "dashboard"

    def create_custom_layout(
        self, name: str, panel_count: int, orientation: str, assignments: List[str]
    ) -> bool:
        """Create a custom layout configuration"""
        if name in self.layouts:
            return False  # Name already exists

        if panel_count < 1 or panel_count > 6:
            return False  # Invalid panel count

        if orientation not in ["horizontal", "vertical", "grid", "mixed"]:
            return False  # Invalid orientation

        # Create equal splitter sizes
        equal_size = 100 // panel_count
        splitter_sizes = [equal_size] * panel_count

        # Adjust for rounding
        remainder = 100 - sum(splitter_sizes)
        if remainder > 0:
            splitter_sizes[0] += remainder

        # Determine minimum panel size based on orientation
        if orientation == "horizontal":
            min_size = (200, 300)
        elif orientation == "vertical":
            min_size = (400, 150)
        else:
            min_size = (250, 200)

        custom_config = LayoutConfig(
            name=f"Custom {name}",
            panel_count=panel_count,
            orientation=orientation,
            default_assignments=assignments[:panel_count],
            description=f"Custom {panel_count}-panel {orientation} layout",
            splitter_sizes=splitter_sizes,
            min_panel_size=min_size,
        )

        self.layouts[name] = custom_config
        return True

    def remove_custom_layout(self, name: str) -> bool:
        """Remove a custom layout"""
        # Don't allow removal of built-in layouts
        builtin_layouts = {
            "2-panel",
            "2-panel-vertical",
            "3-panel",
            "3-panel-mixed",
            "4-panel",
            "4-panel-horizontal",
        }

        if name in builtin_layouts:
            return False

        if name in self.layouts:
            del self.layouts[name]
            return True

        return False

    def export_layout_config(self, layout_name: str) -> Dict[str, Any]:
        """Export layout configuration for saving"""
        config = self.layouts.get(layout_name)
        if not config:
            return {}

        return {
            "name": config.name,
            "panel_count": config.panel_count,
            "orientation": config.orientation,
            "default_assignments": config.default_assignments,
            "description": config.description,
            "splitter_sizes": config.splitter_sizes,
            "min_panel_size": config.min_panel_size,
        }

    def import_layout_config(self, config_data: Dict[str, Any]) -> bool:
        """Import layout configuration from saved data"""
        try:
            required_fields = [
                "name",
                "panel_count",
                "orientation",
                "default_assignments",
                "splitter_sizes",
            ]

            for field in required_fields:
                if field not in config_data:
                    return False

            layout_config = LayoutConfig(
                name=config_data["name"],
                panel_count=config_data["panel_count"],
                orientation=config_data["orientation"],
                default_assignments=config_data["default_assignments"],
                description=config_data.get("description", "Imported layout"),
                splitter_sizes=config_data["splitter_sizes"],
                min_panel_size=tuple(config_data.get("min_panel_size", [300, 200])),
            )

            # Generate unique name if needed
            base_name = config_data["name"]
            counter = 1
            while base_name in self.layouts:
                base_name = f"{config_data['name']}_{counter}"
                counter += 1

            self.layouts[base_name] = layout_config
            return True

        except Exception as e:
            print(f"Error importing layout config: {e}")
            return False


if __name__ == "__main__":
    # Test the layout system
    layouts = PanelLayouts()

    print("Available layouts:")
    for layout_name in layouts.get_available_layouts():
        config = layouts.get_layout_config(layout_name)
        print(f"  {layout_name}: {config['description']}")

    print(f"\nRecommended for 1920x1080: {layouts.get_recommended_layout(1920, 1080)}")
    print(f"Recommended for 3440x1440: {layouts.get_recommended_layout(3440, 1440)}")

    # Test custom layout creation
    success = layouts.create_custom_layout(
        "test", 3, "horizontal", ["dashboard", "monitoring", "logs"]
    )
    print(f"\nCustom layout created: {success}")
