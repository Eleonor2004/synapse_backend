from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Annotated

from app.core.config import SECRET_KEY, ALGORITHM
from app.core.blocklist import BLOCKLIST
from app.models.user import TokenData
from app.models.user import User
# This tells FastAPI where to look for the token ("tokenUrl" is relative to the root)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Decodes the JWT token, validates it, and returns the payload (user data).
    This function serves as a dependency for protected routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        jti: str = payload.get("jti") # Get the unique token ID

        if username is None or jti is None:
            raise credentials_exception
        
        # 2. Check if the token has been blocklisted (logged out)
        if jti in BLOCKLIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token has been revoked (logged out)",
            )

        token_data = TokenData(username=username)
    except JWTError:
        # This catches invalid signatures, expired tokens, etc.
        raise credentials_exception
    
    # In a real app, you would fetch the user from the DB here to ensure they still exist
    # user = get_user_from_db(username=token_data.username)
    # if user is None:
    #     raise credentials_exception
    
    # For now, we'll just return the decoded payload
    return payload


def get_current_admin_user(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """
    A dependency that checks if the current user is an administrator.
    Raises an exception if the user is not an admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have sufficient privileges"
        )
    return current_user