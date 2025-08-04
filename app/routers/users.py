from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from neo4j import Session

# Import all necessary dependencies
from app.dependencies import get_current_admin_user, get_current_user
from app.db.graph_db import get_db_session
from app.crud import user_crud
from app.models.user import User, UserCreate, UserUpdate

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db_session),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    (Admin only) Creates a new user in the system.
    """
    db_user = user_crud.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return user_crud.create_user(db=db, user=user)

@router.get("/", response_model=List[User])
def read_all_users(
    db: Session = Depends(get_db_session),
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    (Admin only) Retrieves a list of all users.
    """
    return user_crud.get_all_users(db)

# --- ROUTE ORDER FIX ---
# The specific path "/me" is now placed BEFORE the dynamic path "/{username}".
# FastAPI will now match this route correctly for any logged-in user.
@router.get("/me", response_model=User)
def read_users_me(
    current_user_payload: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db_session)
):
    """
    Gets the profile of the currently logged-in user (analyst or admin).
    """
    username = current_user_payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    db_user = user_crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
# -------------------------

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
    return None