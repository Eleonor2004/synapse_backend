from neo4j import GraphDatabase, Session
from app.core.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class GraphDB:
    """
    Manages the connection to the Neo4j database.
    This class holds the driver instance and provides methods to get a session.
    """
    def __init__(self):
        # The driver is the main entry point to the database.
        # It is thread-safe and should be created once per application.
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        """Closes the driver connection."""
        if self.driver:
            self.driver.close()

    def get_session(self) -> Session:
        """Returns a new Neo4j session."""
        return self.driver.session()

# Create a single instance of the GraphDB class for the entire application.
db = GraphDB()

# This is a FastAPI dependency.
# It will be called for each request that needs a database session.
# It ensures that the session is properly closed after the request is handled.
def get_db_session():
    """
    FastAPI dependency to get a database session.
    Yields a session to the request and closes it afterwards.
    """
    session = None
    try:
        session = db.get_session()
        yield session
    finally:
        if session:
            session.close()