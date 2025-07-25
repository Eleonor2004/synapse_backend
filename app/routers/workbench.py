import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from typing import Annotated, List
from neo4j import Session

from app.dependencies import get_current_user
from app.db.graph_db import get_db_session
from app.crud import listings_crud
from app.models.listings import ListingSet, ListingSetCreate
from app.models.graph import Graph
from app.routers.graph import format_graph_response # Reuse our formatter
from scripts.ingest_data import ingest_listings_data # Import our ingestion function

router = APIRouter()

def process_and_ingest_data(db: Session, file_contents: bytes, listing_set_id: str):
    """Background task to process a CSV file and ingest its data."""
    # This is a simplified CSV parser. A real app would have more robust error handling.
    try:
        decoded_content = file_contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        listings = [row for row in csv_reader]
        
        # Call our refactored ingestion function
        ingest_listings_data(db, listings, listing_set_id)
    except Exception as e:
        print(f"Error processing file for ListingSet {listing_set_id}: {e}")
        # In a real app, you'd update the ListingSet status to "failed" here.

@router.post("/listings/import", status_code=status.HTTP_202_ACCEPTED)
def import_new_listings(
    background_tasks: BackgroundTasks,
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Uploads a CSV file of listings, creates a new ListingSet for the user,
    and starts the data ingestion in the background.
    """
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    # 1. Create the ListingSet in the database first
    listing_set_create = ListingSetCreate(name=name, description=description)
    new_listing_set = listings_crud.create_listing_set(
        db, listing_set_create, owner_username=current_user["sub"]
    )

    # 2. Add the file processing to a background task
    file_contents = file.file.read()
    background_tasks.add_task(
        process_and_ingest_data, db, file_contents, new_listing_set.id
    )

    return {
        "message": "File upload successful. Ingestion has started in the background.",
        "listing_set": new_listing_set
    }

@router.get("/listings", response_model=List[ListingSet])
def get_my_listing_sets(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Retrieves all ListingSets owned by the current user."""
    return listings_crud.get_user_listing_sets(db, owner_username=current_user["sub"])

@router.post("/visualize", response_model=Graph)
def visualize_data(
    listing_set_ids: List[str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Visualizes the graph data from one or more of the user's specified ListingSets.
    """
    # This query is the core of the security model.
    # It finds all paths within the communications that are PART_OF the specified
    # listing sets, but ONLY if the current user OWNS those sets.
    query = """
    MATCH (u:User {username: $username})-[:OWNS]->(ls:ListingSet)
    WHERE ls.id IN $listing_set_ids
    MATCH p = (c:Communication)-[:PART_OF]->(ls)
    WITH c
    MATCH p = (c)<-[*]-(n)
    RETURN p
    """
    result = db.run(query, username=current_user["sub"], listing_set_ids=listing_set_ids)
    records = list(result)
    if not records:
        return Graph(nodes=[], edges=[])
    return format_graph_response(records)