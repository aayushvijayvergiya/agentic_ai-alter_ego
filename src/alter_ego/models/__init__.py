"""Data models for the Alter Ego application."""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class UserDetails:
    """Model for user contact details."""
    email: str
    name: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class UnknownQuestion:
    """Model for unknown questions that need to be recorded."""
    question: str


@dataclass
class ChatMessage:
    """Model for chat messages."""
    role: str
    content: str
    tool_call_id: Optional[str] = None


@dataclass
class ToolCall:
    """Model for tool call information."""
    id: str
    function_name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """Model for tool execution results."""
    role: str = "tool"
    content: str = ""
    tool_call_id: str = ""
