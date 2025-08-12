from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from neo4j import Session

from app.dependencies import get_current_user
from app.db.graph_db import get_db_session
from app.crud import listings_crud
from app.models.listings import ListingSet, ListingSetUpdate
from app.crud import history_crud
from app.models.history import ActionType


router = APIRouter()

@router.get("/", response_model=List[ListingSet])
def get_user_analyses_history(
    current_user_payload: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db_session)
):
    """
    Gets a list of all analyses (ListingSets) owned by the current user for their history page.
    """
    username = current_user_payload.get("sub")
    return listings_crud.get_user_listing_sets(db, owner_username=username)

@router.put("/{analysis_id}", response_model=ListingSet)
def update_user_analysis(
    analysis_id: str,
    update_data: ListingSetUpdate,
    current_user_payload: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db_session)
):
    """
    Updates the name or description of a specific analysis owned by the current user.
    """
    username = current_user_payload.get("sub")
    updated_set = listings_crud.update_listing_set(db, analysis_id, username, update_data)
    
    if not updated_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found or you do not have permission to edit it."
        )
        history_crud.create_audit_event(
        db, username=username, action=ActionType.UPDATE_ANALYSIS,
        details={"analysis_id": analysis_id, "new_name": update_data.name}
    )

        
    return updated_set

@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_analysis(
    analysis_id: str,
    current_user_payload: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db_session)
):
    """
    Deletes a specific analysis and all its associated data, for the current user.
    """
    username = current_user_payload.get("sub")
    was_deleted = listings_crud.delete_listing_set(db, analysis_id, username)
    
    if not was_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found or you do not have permission to delete it."
        )
        history_crud.create_audit_event(
        db, username=username, action=ActionType.DELETE_ANALYSIS,
        details={"analysis_id": analysis_id}
    )
    
    # On successful deletion, a 204 response has no body, so we return None.
    return None