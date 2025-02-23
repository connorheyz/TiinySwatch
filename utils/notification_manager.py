
from enum import Enum


class NotificationType(Enum):
    OK = 1
    WARNING = 2
    CRITICAL = 3

class NotificationManager:

    _listeners = []

    @classmethod
    def initialize(cls):
        instance = cls()
        return instance
    
    @classmethod
    def addListener(cls, callback):
        cls._listeners.append(callback)
    
    @classmethod
    def notify(cls, message, type):
        for callback in cls._listeners:
            callback(message, type)