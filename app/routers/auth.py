from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from neo4j import Session

from app.core.security import verify_password, create_access_token
from app.models.user import Token
from app.dependencies import get_current_user
from app.db.graph_db import get_db_session
from app.core.blocklist import BLOCKLIST
from app.crud import user_crud # <-- IMPORT THE CRUD MODULE

router = APIRouter()

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db_session) # <-- ADD DB DEPENDENCY
):
    """
    Provides a JWT token for a valid username and password.
    """
    # 1. Find the user in the Neo4j database
    user = user_crud.get_user(db, username=form_data.username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Verify the provided password against the stored hash
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Create the JWT
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    Adds the current user's token JTI to the blocklist.
    """
    jti = current_user.get("jti")
    BLOCKLIST.add(jti)
    return {"message": "Successfully logged out"}