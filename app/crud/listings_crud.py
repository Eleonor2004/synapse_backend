from neo4j import Session
from typing import List
import uuid
from datetime import datetime, timezone
from typing import Optional, List


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

# ... (keep existing imports and functions)

def get_user_dashboard_stats(db: Session, owner_username: str) -> dict:
    """
    Calculates and returns aggregated statistics for a user's dashboard.
    """
    # This single, powerful Cypher query calculates multiple stats at once.
    query = """
    MATCH (u:User {username: $owner_username})-[:OWNS]->(ls:ListingSet)
    // Use OPTIONAL MATCH in case a ListingSet has no Communication nodes yet
    OPTIONAL MATCH (c:Communication)-[:PART_OF]->(ls)
    RETURN
        count(DISTINCT ls) AS total_analyses,
        count(c) AS total_records_processed
    """
    result = db.run(query, owner_username=owner_username)
    record = result.single()

    # The query will always return one row, even if the counts are zero.
    if record:
        return {
            "total_analyses": record["total_analyses"],
            "total_records_processed": record["total_records_processed"]
        }
    
    # Fallback in case something unexpected happens
    return {
        "total_analyses": 0,
        "total_records_processed": 0
    }
    
# ... (keep existing imports and the create_listing_set, get_user_listing_sets functions)
from app.models.listings import ListingSetUpdate

def update_listing_set(
    db: Session,
    listing_set_id: str,
    owner_username: str,
    update_data: ListingSetUpdate
) -> Optional[ListingSet]:
    """
    Updates a ListingSet's properties (e.g., name, description).
    Crucially, it first matches the user to ensure they own the ListingSet
    before performing the update.
    """
    # .model_dump(exclude_unset=True) is vital. It creates a dictionary
    # containing only the fields that the user actually provided in the request.
    data_to_update = update_data.model_dump(exclude_unset=True)

    # If the user sent an empty request body, there's nothing to update.
    if not data_to_update:
        # We can just fetch the existing set and return it.
        result = db.run(
            "MATCH (:User {username: $owner_username})-[:OWNS]->(ls:ListingSet {id: $id}) RETURN ls",
            id=listing_set_id, owner_username=owner_username
        )
        record = result.single()
        if record and record["ls"]:
            data = dict(record["ls"])
            data['createdAt'] = data['createdAt'].to_native()
            return ListingSet.model_validate(data)
        return None

    # The SET clause dynamically updates the node's properties.
    query = """
    MATCH (u:User {username: $owner_username})-[:OWNS]->(ls:ListingSet {id: $id})
    SET ls += $data_to_update
    RETURN ls
    """
    result = db.run(
        query,
        id=listing_set_id,
        owner_username=owner_username,
        data_to_update=data_to_update
    )
    record = result.single()
    if record and record["ls"]:
        data = dict(record["ls"])
        data['createdAt'] = data['createdAt'].to_native()
        return ListingSet.model_validate(data)
    return None # Will return None if the user doesn't own the set or the set doesn't exist

def delete_listing_set(db: Session, listing_set_id: str, owner_username: str) -> bool:
    """
    Deletes a ListingSet and all its associated Communication nodes.
    The initial MATCH ensures a user can only delete analyses they own.
    """
    # This is a powerful, transactional query. It finds the ListingSet owned by the user,
    # finds all Communication nodes linked to it, and then deletes both the
    # communications and the parent ListingSet.
    query = """
    MATCH (u:User {username: $owner_username})-[:OWNS]->(ls:ListingSet {id: $id})
    OPTIONAL MATCH (c:Communication)-[:PART_OF]->(ls)
    DETACH DELETE c, ls
    """
    result = db.run(query, id=listing_set_id, owner_username=owner_username)
    # The result summary tells us how many nodes were actually deleted.
    # If > 0, the deletion was successful.
    return result.summary().counters.nodes_deleted > 0