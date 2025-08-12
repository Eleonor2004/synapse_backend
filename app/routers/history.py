from fastapi import APIRouter, Depends, Query
from typing import Annotated, List
from neo4j import Session

from app.dependencies import get_current_user
from app.db.graph_db import get_db_session
from app.db.graph_db import get_db_session
from app.crud import history_crud
from app.models.history import AuditEvent

router = APIRouter()

@router.get("/actions", response_model=List[AuditEvent])
def read_user_action_history(
    current_user_payload: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    Retrieves a paginated audit trail of actions performed by the current user.
    """
    username = current_user_payload.get("sub")
    return history_crud.get_audit_events_for_user(db, username=username, skip=skip, limit=limit)