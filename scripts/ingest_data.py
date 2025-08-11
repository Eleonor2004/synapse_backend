from neo4j import Session
from datetime import datetime
from app.core.parsing_helpers import find_field_value

def ingest_listings_data(db: Session, listings: list, listing_set_id: str):
    print(f"🚀 Starting ingestion for ListingSet ID: {listing_set_id}...")
    
    processed_count = 0
    # These are the keys from the original Excel file we will look for.
    # These MUST match what your FileUploader is sending.
    caller_fields = ['Numéro Appelant']
    recipient_fields = ['Numéro appelé', 'Numéro appeléA1:F1'] # Handles the malformed key
    duration_fields = ['Durée appel']
    imei_fields = ['IMEI numéro appelant']
    location_fields = ['Localisation', 'Localisation numéro appelant']
    timestamp_fields = ['Date Début appel']

    for i, listing_row in enumerate(listings):
        if not listing_row:
            continue

        try:
            # Find the raw values from the row using the helper
            caller_raw = find_field_value(listing_row, caller_fields)
            recipient_raw = find_field_value(listing_row, recipient_fields)
            timestamp_raw = find_field_value(listing_row, timestamp_fields)
            
            if not caller_raw or not recipient_raw or not timestamp_raw:
                print(f"  -> Skipping row {i+1} due to missing core data (caller, recipient, or timestamp).")
                continue

            # --- THIS IS THE DEFINITIVE FIX ---
            # The date format from your Excel parser is Day/Month/Year.
            # We will parse it with the correct format code: '%d/%m/%Y %H:%M:%S'.
            timestamp = datetime.strptime(str(timestamp_raw), '%d/%m/%Y %H:%M:%S')
            # ------------------------------------

            # Clean and validate the data
            caller = "".join(filter(str.isdigit, caller_raw))
            if caller.startswith('237'): caller = caller[3:]
            
            duration_str = find_field_value(listing_row, duration_fields)
            recipient_is_service = "sms" in str(duration_str).lower() and not any(char.isdigit() for char in recipient_raw)
            
            recipient = "".join(filter(str.isdigit, recipient_raw)) if not recipient_is_service else recipient_raw.strip()
            if recipient.startswith('237'): recipient = recipient[3:]

            if not caller or not recipient or len(caller) < 8:
                continue

            is_sms = "sms" in str(duration_str).lower() or recipient_is_service
            
            location_str = find_field_value(listing_row, location_fields)
            lon, lat = None, None
            if location_str and "Long:" in location_str and "Lat:" in location_str:
                try:
                    lon = float(location_str.split("Long:")[1].split("Lat:")[0].strip())
                    lat = float(location_str.split("Lat:")[1].split("Azimut:")[0].strip())
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