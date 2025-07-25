from neo4j import Session
from typing import Optional, List
from app.models.user import UserInDB, UserCreate
from app.core.security import get_password_hash
from app.models.user import UserUpdate 

def get_user(db: Session, username: str) -> Optional[UserInDB]:
    """
    Retrieves a single user from the database by their username.
    """
    query = "MATCH (u:User {username: $username}) RETURN u"
    result = db.run(query, username=username)
    record = result.single()
    if record and record["u"]:
        user_data = dict(record["u"])
        # The password in the DB is already hashed, so we name it correctly for the model
        user_data["hashed_password"] = user_data.pop("password")
        return UserInDB(**user_data)
    return None

def create_user(db: Session, user: UserCreate) -> UserInDB:
    """
    Creates a new User node in the database.
    """
    hashed_password = get_password_hash(user.password)
    query = """
    CREATE (u:User {
        username: $username,
        full_name: $full_name,
        password: $hashed_password,
        role: $role,
        is_active: $is_active
    })
    RETURN u
    """
    result = db.run(
        query,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role,
        is_active=user.is_active,
    )
    record = result.single()["u"]
    
    user_data = dict(record)
    user_data["hashed_password"] = user_data.pop("password")
    return UserInDB(**user_data)

def get_all_users(db: Session) -> List[UserInDB]:
    """
    Retrieves all users from the database.
    """
    query = "MATCH (u:User) RETURN u"
    result = db.run(query)
    users = []
    for record in result:
        user_data = dict(record["u"])
        user_data["hashed_password"] = user_data.pop("password")
        users.append(UserInDB(**user_data))
    return users


def update_user(db: Session, username: str, user_update: UserUpdate) -> Optional[UserInDB]:
    """
    Updates a user's data in the database.
    """
    # .model_dump(exclude_unset=True) is crucial. It creates a dict with only the
    # fields that were actually provided in the request, so we don't accidentally
    # overwrite existing values with None.
    update_data = user_update.model_dump(exclude_unset=True)

    if not update_data:
        # If no data was provided, just fetch the user and return them
        return get_user(db, username)

    # The SET clause dynamically updates the properties based on the provided data.
    query = """
    MATCH (u:User {username: $username})
    SET u += $update_data
    RETURN u
    """
    result = db.run(query, username=username, update_data=update_data)
    record = result.single()
    if record and record["u"]:
        user_data = dict(record["u"])
        user_data["hashed_password"] = user_data.pop("password")
        return UserInDB(**user_data)
    return None


def delete_user(db: Session, username: str) -> bool:
    """
    Deletes a user from the database.
    Returns True if a user was deleted, False otherwise.
    """
    # We use DETACH DELETE to also remove any relationships the user might have (like :OWNS).
    query = "MATCH (u:User {username: $username}) DETACH DELETE u"
    result = db.run(query, username=username)

    # --- THIS IS THE FIX ---
    # Call .consume() to get the ResultSummary object
    summary = result.consume()
    # The summary object has the counters attribute
    return summary.counters.nodes_deleted > 0
    # -----------------------