from neo4j import Session
from typing import List
import uuid
from datetime import datetime, timezone

from app.models.listings import ListingSet, ListingSetCreate

def create_listing_set(db: Session, listing_set: ListingSetCreate, owner_username: str) -> ListingSet:
    """
    Creates a new ListingSet node and links it to the owner.
    """
    new_id = str(uuid.uuid4())
    # Use a native Python datetime object from the start
    created_at = datetime.now(timezone.utc)

    query = """
    MATCH (u:User {username: $owner_username})
    CREATE (ls:ListingSet {
        id: $id,
        name: $name,
        description: $description,
        owner_username: $owner_username,
        createdAt: $created_at
    })
    CREATE (u)-[:OWNS]->(ls)
    RETURN ls
    """
    result = db.run(
        query,
        owner_username=owner_username,
        id=new_id,
        name=listing_set.name,
        description=listing_set.description,
        created_at=created_at,
    )
    record = result.single()["ls"]

    # --- THIS IS THE FIX ---
    # Convert the Neo4j record (which is like a dict) into a standard Python dict
    data = dict(record)
    # Manually convert the special Neo4j DateTime to a native Python datetime
    data['createdAt'] = data['createdAt'].to_native()
    # Now, validate the clean Python dictionary
    return ListingSet.model_validate(data)
    # -----------------------


def get_user_listing_sets(db: Session, owner_username: str) -> List[ListingSet]:
    """
    Retrieves all ListingSets owned by a specific user.
    """
    query = """
    MATCH (:User {username: $owner_username})-[:OWNS]->(ls:ListingSet)
    RETURN ls ORDER BY ls.createdAt DESC
    """
    result = db.run(query, owner_username=owner_username)
    
    # We need to apply the same fix here for listing existing sets
    listing_sets = []
    for record in result:
        data = dict(record["ls"])
        data['createdAt'] = data['createdAt'].to_native()
        listing_sets.append(ListingSet.model_validate(data))
    return listing_sets