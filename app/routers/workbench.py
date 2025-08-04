import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Annotated, List, Dict, Any
from neo4j import Session

# Corrected imports
from app.dependencies import get_current_user
from app.db.graph_db import  get_db_session
from app.db.graph_db import db_manager # <-- Import the central DB manager
from app.crud import listings_crud
from app.models.listings import ListingSet, ListingSetCreate
from app.models.graph import Graph
from app.routers.graph import format_graph_response
from scripts.ingest_data import ingest_listings_data
from pydantic import BaseModel

router = APIRouter()

class ListingImportRequest(BaseModel):
    name: str
    listings: List[Dict[str, Any]]

# --- CORRECTED BACKGROUND TASK ---
# It no longer accepts a `db` session. It creates its own.
def process_and_ingest_data(listings_data: list, listing_set_id: str):
    """
    Background task to ingest data. It creates and manages its own DB session
    to ensure it's independent of the request that spawned it.
    """
    # Create a new, fresh session specifically for this long-running task
    with db_manager.get_session() as db_session:
        try:
            # Pass the new session to the ingestion function
            ingest_listings_data(db_session, listings_data, listing_set_id)
        except Exception as e:
            print(f"A critical error occurred during background ingestion for {listing_set_id}: {e}")
            # In a production app, you might want to update the ListingSet's status to 'failed' here.

# --- CORRECTED IMPORT ENDPOINT ---
@router.post("/listings/import", status_code=status.HTTP_202_ACCEPTED)
def import_new_listings(
    import_request: ListingImportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session) # This session is ONLY for the fast part of the request
):
    """
    Creates a ListingSet immediately and schedules the data ingestion to run in the background.
    """
    # This part is fast and uses the request's session
    listing_set_create = ListingSetCreate(name=import_request.name)
    new_listing_set = listings_crud.create_listing_set(
        db, listing_set_create, owner_username=current_user["sub"]
    )

    # Schedule the background task.
    # CRITICAL: We do NOT pass the `db` session object from the dependency.
    background_tasks.add_task(
        process_and_ingest_data, import_request.listings, new_listing_set.id
    )
    
    return {
        "message": "Import successful. Ingestion has started in the background.",
        "listing_set": new_listing_set
    }

# --- GET Listings Endpoint (Unchanged) ---
@router.get("/listings", response_model=List[ListingSet])
def get_my_listing_sets(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    return listings_crud.get_user_listing_sets(db, owner_username=current_user["sub"])

# --- Visualization Models and Endpoint (Unchanged) ---
class LocationPoint(BaseModel):
    lat: float
    lng: float
    type: str
    timestamp: str

class GraphResponse(BaseModel):
    network: Graph
    locations: List[LocationPoint]
# ... (imports remain the same)

# --- CORRECTED Visualize Endpoint ---
@router.post("/visualize", response_model=List[Dict[str, Any]])
def visualize_data(
    listing_set_ids: List[str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Fetches the raw listing data (Communication node properties) for a given
    set of ListingSet IDs owned by the current user.
    """
    query = """
    MATCH (u:User {username: $username})-[:OWNS]->(ls:ListingSet)
    WHERE ls.id IN $listing_set_ids
    MATCH (c:Communication)-[:PART_OF]->(ls)
    RETURN properties(c) AS listing
    """
    result = db.run(query, username=current_user["sub"], listing_set_ids=listing_set_ids)
    
    listings = []
    for record in result:
        listing_props = dict(record["listing"])
        # Ensure timestamp is a JSON-serializable ISO string
        if 'timestamp' in listing_props and hasattr(listing_props['timestamp'], 'to_native'):
            listing_props['timestamp'] = listing_props['timestamp'].to_native().isoformat()
        listings.append(listing_props)
        
    return listings