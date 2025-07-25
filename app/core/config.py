import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Neo4j Database Configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

print("Configuration loaded:")
print(f"NEO4J_URI: {'Loaded' if NEO4J_URI else 'Not Found'}")
print(f"NEO4J_USER: {'Loaded' if NEO4J_USER else 'Not Found'}")