from neo4j import GraphDatabase, Session, Driver # Import Driver
from app.core.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class GraphDB:
    def __init__(self):
        # The driver is thread-safe and should be created once per application.
        self.driver: Driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        if self.driver:
            self.driver.close()

    def get_session(self) -> Session:
        return self.driver.session()

# Create a single instance for the entire application.
db_manager = GraphDB()

# Dependency for FastAPI routes
def get_db_session():
    session = None
    try:
        session = db_manager.get_session()
        yield session
    finally:
        if session:
            session.close()