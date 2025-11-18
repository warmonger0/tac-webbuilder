"""
Services Package

This package contains service modules for the TAC WebBuilder server,
including WebSocket connection management and other shared services.
"""

from services.websocket_manager import ConnectionManager

__all__ = ["ConnectionManager"]
