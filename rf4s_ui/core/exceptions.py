#!/usr/bin/env python3
"""
RF4S UI Core Exceptions

Custom exception hierarchy for the RF4S UI application.
Provides specific exception types for different error categories.
"""


class RF4SUIException(Exception):
    """Base exception for RF4S UI application"""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "RF4S_UNKNOWN"
        self.details = details or {}

    def __str__(self):
        return f"[{self.error_code}] {self.message}"


class ComponentException(RF4SUIException):
    """Exception raised by component operations"""

    def __init__(
        self,
        component_name: str,
        message: str,
        error_code: str = None,
        details: dict = None,
    ):
        self.component_name = component_name
        error_code = error_code or f"COMPONENT_{component_name.upper()}_ERROR"
        super().__init__(message, error_code, details)


class BridgeException(RF4SUIException):
    """Exception raised by bridge communication operations"""

    def __init__(
        self,
        bridge_name: str,
        message: str,
        error_code: str = None,
        details: dict = None,
    ):
        self.bridge_name = bridge_name
        error_code = error_code or f"BRIDGE_{bridge_name.upper()}_ERROR"
        super().__init__(message, error_code, details)


class UIException(RF4SUIException):
    """Exception raised by UI operations"""

    def __init__(
        self,
        widget_name: str,
        message: str,
        error_code: str = None,
        details: dict = None,
    ):
        self.widget_name = widget_name
        error_code = error_code or f"UI_{widget_name.upper()}_ERROR"
        super().__init__(message, error_code, details)


class ConfigurationException(RF4SUIException):
    """Exception raised by configuration operations"""

    def __init__(
        self,
        config_key: str,
        message: str,
        error_code: str = None,
        details: dict = None,
    ):
        self.config_key = config_key
        error_code = error_code or "CONFIG_ERROR"
        super().__init__(message, error_code, details)


class ServiceException(RF4SUIException):
    """Exception raised by service registry operations"""

    def __init__(
        self,
        service_name: str,
        message: str,
        error_code: str = None,
        details: dict = None,
    ):
        self.service_name = service_name
        error_code = error_code or f"SERVICE_{service_name.upper()}_ERROR"
        super().__init__(message, error_code, details)


class FeatureException(RF4SUIException):
    """Exception raised by feature operations"""

    def __init__(
        self,
        feature_name: str,
        message: str,
        error_code: str = None,
        details: dict = None,
    ):
        self.feature_name = feature_name
        error_code = error_code or f"FEATURE_{feature_name.upper()}_ERROR"
        super().__init__(message, error_code, details)


class ValidationException(RF4SUIException):
    """Exception raised by validation operations"""

    def __init__(
        self,
        field_name: str,
        message: str,
        error_code: str = None,
        details: dict = None,
    ):
        self.field_name = field_name
        error_code = error_code or "VALIDATION_ERROR"
        super().__init__(message, error_code, details)
