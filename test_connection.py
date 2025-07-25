from neo4j import GraphDatabase
from app.core.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

def check_connection():
    """Checks the connection to the Neo4j database and closes it."""
    driver = None
    try:
        # Attempt to create a driver instance
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # Verify connectivity by fetching server info
        driver.verify_connectivity()
        print("---")
        print("✅ SUCCESS: Connection to Neo4j database established successfully!")
        #print(f"   Database Address: {driver.address}")
        print("---")
    except Exception as e:
        print("---")
        print(f"❌ FAILED: Could not connect to Neo4j database.")
        print(f"   Error: {e}")
        print("   Troubleshooting:")
        print("   1. Is your Neo4j Desktop database running (is it green and 'Active')?")
        print("   2. Are the credentials in your .env file correct (URI, User, Password)?")
        print("---")
    finally:
        if driver:
            driver.close()

if __name__ == "__main__":
    check_connection()