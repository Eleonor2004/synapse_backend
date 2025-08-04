from neo4j import Session
from datetime import datetime
from app.core.parsing_helpers import find_field_value

def ingest_listings_data(db: Session, listings: list, listing_set_id: str):
    print(f"🚀 Starting ingestion for ListingSet ID: {listing_set_id}...")
    
    processed_count = 0
    # Define the possible column names from the Excel file
    caller_fields = ['Numéro Appelant']
    recipient_fields = ['Numéro appelé', 'Numéro appeléA1:F1']
    duration_fields = ['Durée appel']
    imei_fields = ['IMEI numéro appelant']
    location_fields = ['Localisation', 'Localisation numéro appelant']
    timestamp_fields = ['Date Début appel']

    for i, listing_row in enumerate(listings):
        if not listing_row:
            continue

        try:
            caller_raw = find_field_value(listing_row, caller_fields)
            recipient_raw = find_field_value(listing_row, recipient_fields)
            timestamp_raw = find_field_value(listing_row, timestamp_fields)
            
            if not caller_raw or not recipient_raw or not timestamp_raw:
                print(f"  -> Skipping row {i+1} due to missing core data (caller, recipient, or timestamp).")
                continue

            # --- THIS IS THE FIX ---
            # Create a flexible date parsing logic.
            timestamp = None
            possible_formats = [
                '%d/%m/%Y %H:%M:%S',  # The format from your error log (Day/Month/Year)
                '%Y-%m-%d %H:%M:%S',  # A common alternative (Year-Month-Day)
            ]
            
            for fmt in possible_formats:
                try:
                    timestamp = datetime.strptime(str(timestamp_raw), fmt)
                    break # If parsing succeeds, stop trying other formats
                except (ValueError, TypeError):
                    continue # If it fails, try the next format

            # If after trying all formats, timestamp is still None, we can't proceed.
            if timestamp is None:
                print(f"  -> Skipping row {i+1} due to unparseable date format: {timestamp_raw}")
                continue
            # -------------------------

            caller = "".join(filter(str.isdigit, caller_raw))
            if caller.startswith('237'): caller = caller[3:]
            
            recipient_is_service = not any(char.isdigit() for char in recipient_raw)
            recipient = "".join(filter(str.isdigit, recipient_raw)) if not recipient_is_service else recipient_raw.strip()
            if recipient.startswith('237'): recipient = recipient[3:]

            if not caller or not recipient or len(caller) < 8:
                continue

            duration_str = find_field_value(listing_row, duration_fields)
            is_sms = "sms" in str(duration_str).lower() or recipient_is_service
            
            location_str = find_field_value(listing_row, location_fields)
            lon, lat = None, None
            if location_str and "Long:" in location_str and "Lat:" in location_str:
                try:
                    lon = float(location_str.split("Long:")[1].split(" ")[0].strip())
                    lat = float(location_str.split("Lat:")[1].split(" ")[0].strip())
                except (ValueError, IndexError):
                    pass

            query = """
            MATCH (ls:ListingSet {id: $listing_set_id})
            MERGE (caller:Subscriber {phoneNumber: $caller})
            MERGE (callee:Subscriber {phoneNumber: $recipient})
            MERGE (device:Device {imei: $imei})
            MERGE (tower:CellTower {name: $location})
            ON CREATE SET tower.longitude = $lon, tower.latitude = $lat
            CREATE (event:Communication {
                caller_num: $caller,
                callee_num: $recipient,
                timestamp: datetime($timestamp),
                duration_str: $duration_str,
                type: CASE WHEN $is_sms THEN 'SMS' ELSE 'CALL' END,
                imei: $imei,
                location: $location
            })
            CREATE (caller)-[:INITIATED]->(event)
            CREATE (event)-[:IS_DIRECTED_TO]->(callee)
            CREATE (event)-[:USED_DEVICE]->(device)
            CREATE (event)-[:ROUTED_THROUGH]->(tower)
            CREATE (event)-[:PART_OF]->(ls)
            """
            
            db.run(query, {
                "listing_set_id": listing_set_id,
                "caller": caller,
                "recipient": recipient,
                "imei": find_field_value(listing_row, imei_fields),
                "location": location_str,
                "lon": lon,
                "lat": lat,
                "is_sms": is_sms,
                "timestamp": timestamp.isoformat(),
                "duration_str": duration_str
            })
            processed_count += 1
        except Exception as e:
            print(f"  -> FAILED to ingest record {i+1}. Error: {e}. Data: {listing_row}")

    print(f"✅ Ingestion complete. Processed {processed_count} valid records.")