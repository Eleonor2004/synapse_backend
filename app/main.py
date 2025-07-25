from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import graph as graph_router
from app.routers import auth as auth_router # <-- IMPORT NEW ROUTER
from app.db.graph_db import db
from app.routers import users as users_router
from app.routers import workbench as workbench_router
# <-- IMPORT NEW ROUTER
from app.crud import user_crud # <-- Add this
from app.models.user import UserCreate 

app = FastAPI(
    title="SYNAPSE Project API",
    description="API for visualizing and analyzing communication networks.",
    version="1.0.0"
)

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INCLUDE THE NEW ROUTERS ---
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router.router, prefix="/api/v1/users", tags=["Users"]) 
app.include_router(workbench_router.router, prefix="/api/v1/workbench", tags=["Workbench"])
app.include_router(graph_router.router, prefix="/api/v1/graph", tags=["Graph"])

# -------------------------------
@app.on_event("startup")
def on_startup():
    """Create initial admin user on startup if they don't exist."""
    with db.get_session() as session:
        admin_user = user_crud.get_user(session, "admin")
        if not admin_user:
            print("Creating initial admin user...")
            initial_admin = UserCreate(
                username="admin",
                password="admin",
                full_name="Default Admin",
                role="admin"
            )
            user_crud.create_user(session, initial_admin)
            print("Initial admin user created.")
            
@app.on_event("shutdown")
def shutdown_event():
    db.close()
    print("Database connection closed.")

@app.get("/")
def read_root():
    return {"message": "Welcome to the SYNAPSE API. We are ready to go!"}