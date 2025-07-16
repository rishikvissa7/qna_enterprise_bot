# app/services/db.py

from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

POSTGRES_URL = os.getenv("POSTGRES_URL")
engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Checkpoint(Base):
    __tablename__ = "rag_checkpoints"
    user_id = Column(String, primary_key=True)
    state = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
