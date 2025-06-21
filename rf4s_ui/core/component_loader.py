#!/usr/bin/env python3
"""
RF4S UI Component Loader

Dynamic component loading system for modular architecture.
Handles component discovery, loading, and initialization.
"""

import importlib
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .event_manager import EventManager
from .exceptions import ComponentException
from .service_registry import ServiceRegistry


class ComponentLoader:
    """
    Dynamic component loader for modular architecture

    Discovers and loads components from the components directory,
    handles dependency resolution and initialization order.
    """

    def __init__(self, components_path: Path = None):
        self.components_path = (
            components_path or Path(__file__).parent.parent / "components"
        )
        self.loaded_components: Dict[str, Any] = {}
        self.component_metadata: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        self.service_registry = ServiceRegistry()
        self.event_manager = EventManager()

    def discover_components(self) -> List[str]:
        """Discover available components"""
        try:
            components = []

            if not self.components_path.exists():
                self.logger.warning(
                    f"Components path does not exist: {self.components_path}"
                )
                return components

            for item in self.components_path.iterdir():
                if item.is_dir() and not item.name.startswith("_"):
                    # Check if it has an __init__.py file
                    init_file = item / "__init__.py"
                    if init_file.exists():
                        components.append(item.name)
                        self.logger.debug(f"Discovered component: {item.name}")

            return components

        except Exception as e:
            raise ComponentException("loader", f"Failed to discover components: {e}")

    def load_component(self, component_name: str) -> Any:
        """Load a specific component"""
        try:
            if component_name in self.loaded_components:
                return self.loaded_components[component_name]

            # Import the component module
            module_path = f"components.{component_name}"

            # Add the parent directory to sys.path if not already there
            parent_path = str(self.components_path.parent)
            if parent_path not in sys.path:
                sys.path.insert(0, parent_path)

            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                raise ComponentException(
                    component_name, f"Failed to import component: {e}"
                )

            # Look for component class or factory function
            component_instance = self._create_component_instance(module, component_name)

            if component_instance:
                self.loaded_components[component_name] = component_instance
                self._register_component_services(component_name, component_instance)
                self.logger.info(f"Loaded component: {component_name}")
                return component_instance
            else:
                raise ComponentException(
                    component_name, "No valid component class or factory found"
                )

        except Exception as e:
            if isinstance(e, ComponentException):
                raise
            raise ComponentException(component_name, f"Failed to load component: {e}")

    def _create_component_instance(self, module: Any, component_name: str) -> Any:
        """Create component instance from module"""
        try:
            # Look for specific patterns
            patterns = [
                f"{component_name.title().replace('_', '')}",  # CamelCase
                f"{component_name.upper()}",  # UPPERCASE
                "Component",  # Generic Component class
                "create_component",  # Factory function
                "get_component",  # Getter function
            ]

            for pattern in patterns:
                if hasattr(module, pattern):
                    attr = getattr(module, pattern)

                    if inspect.isclass(attr):
                        # It's a class, instantiate it
                        return attr()
                    elif callable(attr):
                        # It's a function, call it
                        return attr()

            # Look for any class that might be the component
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if not name.startswith("_") and obj.__module__ == module.__name__:
                    return obj()

            return None

        except Exception as e:
            raise ComponentException(
                component_name, f"Failed to create component instance: {e}"
            )

    def _register_component_services(
        self, component_name: str, component_instance: Any
    ):
        """Register component services with the service registry"""
        try:
            # Register the component itself
            self.service_registry.register_instance(component_name, component_instance)

            # Check if component has services to register
            if hasattr(component_instance, "register_services"):
                component_instance.register_services(self.service_registry)

            # Check if component has event subscriptions
            if hasattr(component_instance, "register_events"):
                component_instance.register_events(self.event_manager)

        except Exception as e:
            self.logger.error(f"Error registering services for {component_name}: {e}")

    def load_all_components(self) -> Dict[str, Any]:
        """Load all discovered components"""
        try:
            components = self.discover_components()
            loaded = {}

            for component_name in components:
                try:
                    component = self.load_component(component_name)
                    loaded[component_name] = component
                except Exception as e:
                    self.logger.error(f"Failed to load component {component_name}: {e}")

            self.logger.info(f"Loaded {len(loaded)} components")
            return loaded

        except Exception as e:
            raise ComponentException("loader", f"Failed to load all components: {e}")

    def unload_component(self, component_name: str):
        """Unload a component"""
        try:
            if component_name in self.loaded_components:
                component = self.loaded_components[component_name]

                # Call cleanup if available
                if hasattr(component, "cleanup"):
                    component.cleanup()

                # Unregister from service registry
                if self.service_registry.has_service(component_name):
                    self.service_registry.unregister_service(component_name)

                del self.loaded_components[component_name]
                self.logger.info(f"Unloaded component: {component_name}")

        except Exception as e:
            raise ComponentException(component_name, f"Failed to unload component: {e}")

    def reload_component(self, component_name: str) -> Any:
        """Reload a component"""
        try:
            self.unload_component(component_name)

            # Reload the module
            module_path = f"components.{component_name}"
            if module_path in sys.modules:
                importlib.reload(sys.modules[module_path])

            return self.load_component(component_name)

        except Exception as e:
            raise ComponentException(component_name, f"Failed to reload component: {e}")

    def get_component(self, component_name: str) -> Any:
        """Get a loaded component"""
        if component_name in self.loaded_components:
            return self.loaded_components[component_name]
        else:
            # Try to load it
            return self.load_component(component_name)

    def is_loaded(self, component_name: str) -> bool:
        """Check if a component is loaded"""
        return component_name in self.loaded_components

    def list_loaded_components(self) -> List[str]:
        """List all loaded components"""
        return list(self.loaded_components.keys())

    def get_component_info(self, component_name: str) -> Dict[str, Any]:
        """Get information about a component"""
        try:
            if component_name not in self.loaded_components:
                return {}

            component = self.loaded_components[component_name]

            info = {
                "name": component_name,
                "type": type(component).__name__,
                "module": type(component).__module__,
                "loaded": True,
                "has_cleanup": hasattr(component, "cleanup"),
                "has_services": hasattr(component, "register_services"),
                "has_events": hasattr(component, "register_events"),
            }

            # Get additional metadata if available
            if hasattr(component, "get_metadata"):
                info["metadata"] = component.get_metadata()

            return info

        except Exception as e:
            self.logger.error(f"Error getting component info for {component_name}: {e}")
            return {}

    def cleanup_all(self):
        """Cleanup all loaded components"""
        try:
            for component_name in list(self.loaded_components.keys()):
                self.unload_component(component_name)

            self.loaded_components.clear()
            self.logger.info("All components cleaned up")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
