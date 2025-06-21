#!/usr/bin/env python3
"""
RF4S UI Core Module

Core infrastructure components for the RF4S UI application.
Provides foundational services for modular architecture.
"""

from .application import RF4SApplication
from .component_loader import ComponentLoader
from .event_manager import (Event, EventManager, get_event_history, publish,
                            subscribe, unsubscribe)
from .exceptions import (BridgeException, ComponentException,
                         ConfigurationException, FeatureException,
                         RF4SUIException, ServiceException, UIException,
                         ValidationException)
from .service_registry import (ServiceRegistry, get_service, has_service,
                               register_factory, register_instance,
                               register_service)

__all__ = [
    # Main application
    "RF4SApplication",
    # Service registry
    "ServiceRegistry",
    "register_service",
    "register_factory",
    "register_instance",
    "get_service",
    "has_service",
    # Event system
    "EventManager",
    "Event",
    "subscribe",
    "unsubscribe",
    "publish",
    "get_event_history",
    # Component loading
    "ComponentLoader",
    # Exceptions
    "RF4SUIException",
    "ComponentException",
    "BridgeException",
    "UIException",
    "ConfigurationException",
    "ServiceException",
    "FeatureException",
    "ValidationException",
]

# Version information
__version__ = "1.0.0"
__author__ = "RF4S UI Team"
__description__ = "RF4S PyQt-Fluent-Widgets UI Core Module"
