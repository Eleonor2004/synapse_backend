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