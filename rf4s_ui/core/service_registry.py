#!/usr/bin/env python3
"""
RF4S UI Service Registry

Implements the service locator pattern for dependency injection.
Manages component registration, resolution, and lifecycle.
"""

import logging
from threading import Lock
from typing import Any, Callable, Dict, Optional, Type

from .exceptions import ServiceException


class ServiceRegistry:
    """
    Singleton service registry for dependency injection

    Provides centralized service registration and resolution
    with thread-safe operations and lifecycle management.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._services: Dict[str, Any] = {}
            self._factories: Dict[str, Callable] = {}
            self._singletons: Dict[str, Any] = {}
            self._dependencies: Dict[str, list] = {}
            self.logger = logging.getLogger(__name__)
            self._initialized = True

    def register_service(self, name: str, service_class: Type, singleton: bool = True):
        """Register a service class"""
        try:
            with self._lock:
                if singleton:
                    self._singletons[
                        name
                    ] = None  # Will be instantiated on first access
                self._services[name] = service_class
                self.logger.info(f"Registered service: {name}")
        except Exception as e:
            raise ServiceException(name, f"Failed to register service: {e}")

    def register_factory(self, name: str, factory: Callable):
        """Register a factory function for service creation"""
        try:
            with self._lock:
                self._factories[name] = factory
                self.logger.info(f"Registered factory: {name}")
        except Exception as e:
            raise ServiceException(name, f"Failed to register factory: {e}")

    def register_instance(self, name: str, instance: Any):
        """Register a service instance directly"""
        try:
            with self._lock:
                self._singletons[name] = instance
                self.logger.info(f"Registered instance: {name}")
        except Exception as e:
            raise ServiceException(name, f"Failed to register instance: {e}")

    def get_service(self, name: str) -> Any:
        """Get a service instance"""
        try:
            with self._lock:
                # Check if singleton instance exists
                if name in self._singletons:
                    if self._singletons[name] is None:
                        # Instantiate singleton
                        if name in self._services:
                            self._singletons[name] = self._services[name]()
                        elif name in self._factories:
                            self._singletons[name] = self._factories[name]()
                        else:
                            raise ServiceException(name, "Service not registered")
                    return self._singletons[name]

                # Check if service class is registered
                if name in self._services:
                    return self._services[name]()

                # Check if factory is registered
                if name in self._factories:
                    return self._factories[name]()

                raise ServiceException(name, "Service not found")

        except Exception as e:
            if isinstance(e, ServiceException):
                raise
            raise ServiceException(name, f"Failed to get service: {e}")

    def has_service(self, name: str) -> bool:
        """Check if a service is registered"""
        return (
            name in self._services
            or name in self._factories
            or name in self._singletons
        )

    def unregister_service(self, name: str):
        """Unregister a service"""
        try:
            with self._lock:
                if name in self._services:
                    del self._services[name]
                if name in self._factories:
                    del self._factories[name]
                if name in self._singletons:
                    del self._singletons[name]
                if name in self._dependencies:
                    del self._dependencies[name]
                self.logger.info(f"Unregistered service: {name}")
        except Exception as e:
            raise ServiceException(name, f"Failed to unregister service: {e}")

    def add_dependency(self, service_name: str, dependency_name: str):
        """Add a dependency relationship between services"""
        try:
            with self._lock:
                if service_name not in self._dependencies:
                    self._dependencies[service_name] = []
                if dependency_name not in self._dependencies[service_name]:
                    self._dependencies[service_name].append(dependency_name)
                    self.logger.debug(
                        f"Added dependency: {service_name} -> {dependency_name}"
                    )
        except Exception as e:
            raise ServiceException(service_name, f"Failed to add dependency: {e}")

    def get_dependencies(self, service_name: str) -> list:
        """Get dependencies for a service"""
        return self._dependencies.get(service_name, [])

    def initialize_services(self):
        """Initialize all registered singleton services"""
        try:
            for name in list(self._singletons.keys()):
                if self._singletons[name] is None:
                    self.get_service(name)
            self.logger.info("All services initialized")
        except Exception as e:
            raise ServiceException("registry", f"Failed to initialize services: {e}")

    def shutdown_services(self):
        """Shutdown all services"""
        try:
            with self._lock:
                for name, instance in self._singletons.items():
                    if instance and hasattr(instance, "shutdown"):
                        try:
                            instance.shutdown()
                            self.logger.debug(f"Shutdown service: {name}")
                        except Exception as e:
                            self.logger.error(f"Error shutting down {name}: {e}")

                self._services.clear()
                self._factories.clear()
                self._singletons.clear()
                self._dependencies.clear()
                self.logger.info("All services shutdown")
        except Exception as e:
            raise ServiceException("registry", f"Failed to shutdown services: {e}")

    def list_services(self) -> Dict[str, str]:
        """List all registered services"""
        services = {}
        for name in self._services:
            services[name] = "class"
        for name in self._factories:
            services[name] = "factory"
        for name in self._singletons:
            services[name] = "singleton"
        return services


# Convenience functions for global access
_registry = ServiceRegistry()


def register_service(name: str, service_class: Type, singleton: bool = True):
    """Register a service globally"""
    _registry.register_service(name, service_class, singleton)


def register_factory(name: str, factory: Callable):
    """Register a factory globally"""
    _registry.register_factory(name, factory)


def register_instance(name: str, instance: Any):
    """Register an instance globally"""
    _registry.register_instance(name, instance)


def get_service(name: str) -> Any:
    """Get a service globally"""
    return _registry.get_service(name)


def has_service(name: str) -> bool:
    """Check if service exists globally"""
    return _registry.has_service(name)
