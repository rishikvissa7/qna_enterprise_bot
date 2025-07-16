# app/main.py

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.api.query_router import router as query_router
from app.services.db import init_db

init_db()
app = FastAPI()
app.include_router(query_router)
