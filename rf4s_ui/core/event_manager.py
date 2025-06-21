#!/usr/bin/env python3
"""
RF4S UI Event Manager

Implements event-driven architecture for component communication.
Provides publish-subscribe pattern with type-safe event handling.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

from .exceptions import ServiceException


@dataclass
class Event:
    """Event data structure"""

    name: str
    data: Any
    timestamp: datetime
    source: Optional[str] = None
    event_id: Optional[str] = None


class EventManager:
    """
    Event manager for publish-subscribe communication

    Provides thread-safe event publishing and subscription
    with support for event filtering and priority handling.
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
            self._subscribers: Dict[str, List[Callable]] = {}
            self._event_history: List[Event] = []
            self._max_history = 1000
            self.logger = logging.getLogger(__name__)
            self._initialized = True

    def subscribe(self, event_name: str, callback: Callable, priority: int = 0):
        """Subscribe to an event"""
        try:
            with self._lock:
                if event_name not in self._subscribers:
                    self._subscribers[event_name] = []

                # Add callback with priority (higher priority = earlier execution)
                callback_info = {"callback": callback, "priority": priority}
                self._subscribers[event_name].append(callback_info)

                # Sort by priority (descending)
                self._subscribers[event_name].sort(
                    key=lambda x: x["priority"], reverse=True
                )

                self.logger.debug(f"Subscribed to event: {event_name}")
        except Exception as e:
            raise ServiceException(
                "event_manager", f"Failed to subscribe to {event_name}: {e}"
            )

    def unsubscribe(self, event_name: str, callback: Callable):
        """Unsubscribe from an event"""
        try:
            with self._lock:
                if event_name in self._subscribers:
                    self._subscribers[event_name] = [
                        cb_info
                        for cb_info in self._subscribers[event_name]
                        if cb_info["callback"] != callback
                    ]

                    if not self._subscribers[event_name]:
                        del self._subscribers[event_name]

                    self.logger.debug(f"Unsubscribed from event: {event_name}")
        except Exception as e:
            raise ServiceException(
                "event_manager", f"Failed to unsubscribe from {event_name}: {e}"
            )

    def publish(self, event_name: str, data: Any = None, source: str = None):
        """Publish an event"""
        try:
            event = Event(
                name=event_name,
                data=data,
                timestamp=datetime.now(),
                source=source,
                event_id=f"{event_name}_{datetime.now().timestamp()}",
            )

            # Add to history
            with self._lock:
                self._event_history.append(event)
                if len(self._event_history) > self._max_history:
                    self._event_history.pop(0)

            # Notify subscribers
            self._notify_subscribers(event)

            self.logger.debug(f"Published event: {event_name}")

        except Exception as e:
            raise ServiceException(
                "event_manager", f"Failed to publish {event_name}: {e}"
            )

    def _notify_subscribers(self, event: Event):
        """Notify all subscribers of an event"""
        try:
            subscribers = self._subscribers.get(event.name, [])

            for subscriber_info in subscribers:
                try:
                    callback = subscriber_info["callback"]
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in event callback for {event.name}: {e}")

        except Exception as e:
            self.logger.error(f"Error notifying subscribers for {event.name}: {e}")

    def get_event_history(
        self, event_name: str = None, limit: int = 100
    ) -> List[Event]:
        """Get event history"""
        try:
            with self._lock:
                if event_name:
                    filtered_events = [
                        event
                        for event in self._event_history
                        if event.name == event_name
                    ]
                    return filtered_events[-limit:]
                else:
                    return self._event_history[-limit:]
        except Exception as e:
            self.logger.error(f"Error getting event history: {e}")
            return []

    def clear_history(self):
        """Clear event history"""
        try:
            with self._lock:
                self._event_history.clear()
                self.logger.info("Event history cleared")
        except Exception as e:
            self.logger.error(f"Error clearing event history: {e}")

    def get_subscribers(self, event_name: str) -> int:
        """Get number of subscribers for an event"""
        return len(self._subscribers.get(event_name, []))

    def list_events(self) -> List[str]:
        """List all events with subscribers"""
        return list(self._subscribers.keys())

    def has_subscribers(self, event_name: str) -> bool:
        """Check if an event has subscribers"""
        return (
            event_name in self._subscribers and len(self._subscribers[event_name]) > 0
        )


# Convenience functions for global access
_event_manager = EventManager()


def subscribe(event_name: str, callback: Callable, priority: int = 0):
    """Subscribe to an event globally"""
    _event_manager.subscribe(event_name, callback, priority)


def unsubscribe(event_name: str, callback: Callable):
    """Unsubscribe from an event globally"""
    _event_manager.unsubscribe(event_name, callback)


def publish(event_name: str, data: Any = None, source: str = None):
    """Publish an event globally"""
    _event_manager.publish(event_name, data, source)


def get_event_history(event_name: str = None, limit: int = 100) -> List[Event]:
    """Get event history globally"""
    return _event_manager.get_event_history(event_name, limit)
