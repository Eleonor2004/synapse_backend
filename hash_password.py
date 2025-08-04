# We need to import the function from our security module
from app.core.security import get_password_hash

# The password we want to hash
plain_password = "adminpassword"

# Generate the hash
hashed_password = get_password_hash(plain_password)

# Print it out so we can copy it
print("Copy this entire hashed password:")
print("---------------------------------")
print(hashed_password)
print("---------------------------------")