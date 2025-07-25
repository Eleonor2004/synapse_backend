# This is a simple in-memory set to store the JTI of logged-out tokens.
# ---
# IMPORTANT: In a real-world, multi-process production environment,
# you would replace this with a shared, persistent cache like Redis.
# This in-memory solution will be reset every time the server restarts.
# ---
BLOCKLIST = set()