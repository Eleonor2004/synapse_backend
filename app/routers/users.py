from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from neo4j import Session

from app.db.graph_db import get_db_session
from app.dependencies import get_current_admin_user
from app.crud import user_crud
# Import the new UserUpdate model
from app.models.user import User, UserCreate, UserUpdate

router = APIRouter()

# --- POST and GET / (Unchanged) ---
@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db_session),
    admin_user: dict = Depends(get_current_admin_user)
):
    db_user = user_crud.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return user_crud.create_user(db=db, user=user)

@router.get("/", response_model=List[User])
def read_all_users(
    db: Session = Depends(get_db_session),
    admin_user: dict = Depends(get_current_admin_user)
):
    return user_crud.get_all_users(db)

# --- NEW ENDPOINTS ---

@router.get("/{username}", response_model=User)
def read_user_by_username(
    username: str,
    db: Session = Depends(get_db_session),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    (Admin only) Retrieves a single user by their username.
    """
    db_user = user_crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{username}", response_model=User)
def update_existing_user(
    username: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db_session),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    (Admin only) Updates a user's information.
    """
    updated_user = user_crud.update_user(db, username, user_update)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_user(
    username: str,
    db: Session = Depends(get_db_session),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    (Admin only) Deletes a user from the system.
    """
    was_deleted = user_crud.delete_user(db, username)
    if not was_deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return None # Return nothing on success for 204