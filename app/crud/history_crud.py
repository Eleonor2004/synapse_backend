from neo4j import Session
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone
import json # Import json at the top

from app.models.history import AuditEvent, ActionType

def create_audit_event(
    db: Session,
    username: str,
    action: ActionType,
    details: Dict[str, Any],
    status: str = "SUCCESS"
):
    """
    Creates an AuditEvent node and links it to the user who performed the action.
    """
    try:
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        
        query = """
        MATCH (u:User {username: $username})
        CREATE (a:AuditEvent {
            id: $id,
            username: $username,
            action_type: $action_type,
            timestamp: $timestamp,
            details_json: $details_json,
            status: $status
        })
        CREATE (u)-[:PERFORMED]->(a)
        """
        details_json = json.dumps(details)
        
        db.run(
            query,
            username=username,
            id=event_id,
            action_type=action.value,
            timestamp=timestamp,
            details_json=details_json,
            status=status
        )
    except Exception as e:
        print(f"CRITICAL: Failed to create audit event. Error: {e}")

def get_audit_events_for_user(db: Session, username: str, skip: int = 0, limit: int = 100) -> List[AuditEvent]:
    """
    Retrieves a paginated list of audit events for a specific user.
    """
    query = """
    MATCH (:User {username: $username})-[:PERFORMED]->(a:AuditEvent)
    RETURN a
    ORDER BY a.timestamp DESC
    SKIP $skip
    LIMIT $limit
    """
    result = db.run(query, username=username, skip=skip, limit=limit)
    
    events = []
    for record in result:
        event_data = dict(record["a"])
        
        # --- THIS IS THE FIX ---
        # 1. Deserialize the details from a JSON string back into a dict.
        event_data["details"] = json.loads(event_data.pop("details_json", "{}"))
        
        # 2. Manually convert the special Neo4j DateTime to a native Python datetime.
        if 'timestamp' in event_data and hasattr(event_data['timestamp'], 'to_native'):
            event_data['timestamp'] = event_data['timestamp'].to_native()
        # -----------------------

        # Now that all fields are standard Python types, Pydantic can validate them.
        events.append(AuditEvent(**event_data))
            
    return events