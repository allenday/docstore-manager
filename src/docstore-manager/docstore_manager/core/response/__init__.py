"""Module for defining response structures."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, List

@dataclass
class Response:
    """Generic response container."""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

__all__ = ['Response'] 