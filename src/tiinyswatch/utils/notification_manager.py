from enum import Enum
from typing import List, Callable, Tuple


class NotificationType(Enum):
    """Enumeration of notification types for the application."""
    OK = 1  # Success notification
    WARNING = 2  # Warning notification
    CRITICAL = 3  # Critical error notification


class NotificationManager:
    """
    Manages notifications throughout the application.
    
    Provides a centralized system for dispatching notifications to 
    registered listeners.
    """
    _listeners: List[Callable[[str, NotificationType], None]] = []

    @classmethod
    def initialize(cls) -> 'NotificationManager':
        """Initialize the notification manager (singleton-like pattern)."""
        instance = cls()
        return instance
    
    @classmethod
    def addListener(cls, callback: Callable[[str, NotificationType], None]) -> None:
        """
        Register a listener to receive notifications.
        
        Args:
            callback: Function to call with message and notification type
        """
        cls._listeners.append(callback)
    
    @classmethod
    def notify(cls, message: str, type_: NotificationType) -> None:
        """
        Send a notification to all registered listeners.
        
        Args:
            message: The notification message
            type_: The notification type (OK, WARNING, CRITICAL)
        """
        for callback in cls._listeners:
            callback(message, type_)

# Make sure we explicitly export these classes
__all__ = ['NotificationManager', 'NotificationType'] 