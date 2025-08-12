from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class ListingSetBase(BaseModel):
    name: str
    description: Optional[str] = None

class ListingSetCreate(ListingSetBase):
    pass

class ListingSet(ListingSetBase):
    id: str
    owner_username: str
    createdAt: datetime

    class Config:
        from_attributes = True # Allows creating model from ORM objects
class ListingSetUpdate(BaseModel):
    """
    Defines the fields a user can update on an existing ListingSet.
    All fields are optional to allow for partial updates (e.g., changing only the name).
    """
    name: Optional[str] = None
    description: Optional[str] = None