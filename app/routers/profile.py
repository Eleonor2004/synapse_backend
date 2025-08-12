from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from neo4j import Session

from app.dependencies import get_current_user
from app.db.graph_db import  get_db_session

from app.crud import user_crud
from app.models.user import Profile, ProfileUpdate, User

router = APIRouter()

@router.get("/me", response_model=Profile)
def read_current_user_profile(
    current_user_payload: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db_session)
):
    """
    Gets the complete profile of the currently logged-in user,
    including their analysis count.
    """
    username = current_user_payload.get("sub")
    
    # 1. Fetch the base user data from the database
    db_user = user_crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. Fetch the user's analysis count
    analysis_count = user_crud.count_user_analyses(db, username=username)
    
    # 3. Combine the data into our Profile response model
    profile_data = db_user.model_dump()
    profile_data["analysis_count"] = analysis_count
    
    return Profile(**profile_data)

@router.put("/me", response_model=Profile)
def update_current_user_profile(
    profile_update_data: ProfileUpdate,
    current_user_payload: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db_session)
):
    """
    Updates the profile (e.g., full_name) of the currently logged-in user.
    """
    username = current_user_payload.get("sub")
    
    # The update_user function in user_crud is already suitable for this
    updated_user = user_crud.update_user(db, username=username, user_update=profile_update_data)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found, could not update profile.")

    # After updating, fetch the new analysis count and return the full profile
    analysis_count = user_crud.count_user_analyses(db, username=username)
    profile_data = updated_user.model_dump()
    profile_data["analysis_count"] = analysis_count

    return Profile(**profile_data)