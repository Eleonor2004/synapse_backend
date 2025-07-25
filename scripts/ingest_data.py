from neo4j import Session
from datetime import datetime

def ingest_listings_data(db: Session, listings: list, listing_set_id: str):
    """
    Ingests a list of listing data into the database, linking it to a specific ListingSet.
    """
    print(f"🚀 Starting ingestion for ListingSet ID: {listing_set_id}...")
    
    processed_count = 0
    for i, listing in enumerate(listings):
        # Add a check to ensure the row is not empty and has the required key.
        if not listing or not listing.get("timestamp_str"):
            # --- THIS IS THE IMPROVEMENT ---
            # Print the problematic row to see what keys were actually found
            print(f"  -> Skipping empty or invalid row {i+1}. Found keys: {list(listing.keys()) if listing else 'None'}")
            # ------------------------------
            continue 

        try:
            timestamp = datetime.strptime(listing["timestamp_str"], "%d/%m/%Y %H:%M:%S")
            is_sms = listing["duration_str"] == "SMS"
            
            query = """
            MATCH (ls:ListingSet {id: $listing_set_id})
            MERGE (caller:Subscriber {phoneNumber: $caller_num})
            MERGE (callee:Subscriber {phoneNumber: $callee_num})
            MERGE (device:Device {imei: $imei})
            MERGE (tower:CellTower {name: $tower_name})
            ON CREATE SET tower.longitude = $tower_long, tower.latitude = $tower_lat
            CREATE (event:Communication {
                type: CASE WHEN $is_sms THEN 'SMS' ELSE 'CALL' END,
                timestamp: $timestamp,
                duration: $duration_str
            })
            CREATE (caller)-[:INITIATED]->(event)
            CREATE (event)-[:IS_DIRECTED_TO]->(callee)
            CREATE (event)-[:USED_DEVICE]->(device)
            CREATE (event)-[:ROUTED_THROUGH]->(tower)
            CREATE (event)-[:PART_OF]->(ls)
            """
            
            db.run(query, {
                "listing_set_id": listing_set_id,
                "caller_num": listing.get("caller_num"),
                "callee_num": listing.get("callee_num"),
                "imei": listing.get("imei"),
                "tower_name": listing.get("tower_name"),
                "tower_long": listing.get("tower_long"),
                "tower_lat": listing.get("tower_lat"),
                "is_sms": is_sms,
                "timestamp": timestamp,
                "duration_str": listing.get("duration_str")
            })
            processed_count += 1
            print(f"  -> Ingested record {i+1} (Total processed: {processed_count})")
        except Exception as e:
            print(f"  -> FAILED to ingest record {i+1}. Error: {e}")

    print(f"✅ Ingestion complete. Processed {processed_count} valid records.")