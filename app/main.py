from fastapi import FastAPI
from app.api.query_router import router as query_router
from dotenv import load_dotenv
load_dotenv()


app = FastAPI()
app.include_router(query_router)