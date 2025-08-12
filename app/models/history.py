from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from enum import Enum

class ActionType(str, Enum):
    """Enumeration for the types of actions that can be audited."""
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    CREATE_ANALYSIS = "CREATE_ANALYSIS"
    VIEW_ANALYSIS = "VIEW_ANALYSIS"
    UPDATE_ANALYSIS = "UPDATE_ANALYSIS"
    DELETE_ANALYSIS = "DELETE_ANALYSIS"
    CREATE_USER = "CREATE_USER"
    UPDATE_USER = "UPDATE_USER"
    DELETE_USER = "DELETE_USER"
    UPDATE_PROFILE = "UPDATE_PROFILE"

class AuditEvent(BaseModel):
    """
    Represents a single, logged historical event.
    """
    id: str
    username: str
    action_type: ActionType
    timestamp: datetime
    details: Dict[str, Any]
    status: str # e.g., "SUCCESS", "FAILURE"