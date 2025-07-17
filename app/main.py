# app/main.py

# Load environment variables
from dotenv import load_dotenv
load_dotenv()  # Loads variables from a .env file

# FastAPI setup
from fastapi import FastAPI

# Import the API router that defines our `/ask` endpoint
from app.api.query_router import router as query_router

# Import and run the database initialization function
from app.db.db import init_db
init_db()  # Creates tables if they don’t already exist

# Create FastAPI app instance
app = FastAPI()

# Register API routes used for handling user queries
app.include_router(query_router)
