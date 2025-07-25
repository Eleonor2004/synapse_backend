from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """Pydantic model for the access token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Pydantic model for the data encoded in the token."""
    username: Optional[str] = None

class User(BaseModel):
    """Basic user model for API responses (omits password)."""
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool

class UserInDB(User):
    """User model as it is stored in the database (includes hashed password)."""
    hashed_password: str
    
# ... (keep existing classes Token, TokenData, User, UserInDB)

class UserCreate(BaseModel):
    """Model for creating a new user, accepts a plaintext password."""
    username: str
    full_name: Optional[str] = None
    password: str
    role: str = "analyst"
    is_active: bool = True
    
# ... (keep existing classes)

class UserUpdate(BaseModel):
    """Model for updating a user. All fields are optional."""
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None