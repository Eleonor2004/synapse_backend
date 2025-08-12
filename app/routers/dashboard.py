from fastapi import APIRouter, Depends
from typing import Annotated
from neo4j import Session

from app.db.graph_db import  get_db_session
from app.dependencies import get_current_user
from app.crud import listings_crud
from app.models.dashboard import UserDashboardStats

router = APIRouter()

@router.get("/stats", response_model=UserDashboardStats)
def read_user_dashboard_statistics(
    current_user_payload: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db_session)
):
    """
    Retrieves aggregated statistics for the currently logged-in user's dashboard.
    """
    username = current_user_payload.get("sub")
    
    # Call the new CRUD function to get the stats from the database
    stats_data = listings_crud.get_user_dashboard_stats(db, owner_username=username)
    
    # Return the data, which will be validated by the UserDashboardStats model
    return UserDashboardStats(**stats_data)