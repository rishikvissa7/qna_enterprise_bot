# app/services/db.py

# SQLAlchemy components to define tables and interact with the database
from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Built-in modules
import os
from datetime import datetime

# Database Configuration and Connection
# Load the Postgres database URL from environment variables
POSTGRES_URL = os.getenv("POSTGRES_URL")

# Create a connection engine to the PostgreSQL database
engine = create_engine(POSTGRES_URL)

# Create a session factory — used to interact with the database in a transaction-safe way
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class to define our ORM models
Base = declarative_base()


# Table 1: Conversation Turn History
class ConversationTurn(Base):
    """
    Represents a single turn in a conversation
    Stores:
    - user_id: Who is speaking
    - role: 'user' or 'assistant'
    - content: What was said
    - timestamp: When it was said
    """
    __tablename__ = "conversation_turns"

    id = Column(Integer, primary_key=True, index=True)  # Unique ID for each turn
    user_id = Column(String, index=True)  # The user the turn belongs to
    role = Column(String)  # Either 'user' or 'assistant'
    content = Column(Text)  # The message content
    timestamp = Column(DateTime, default=datetime.utcnow)  # Auto-timestamp when saved


# Table 2: Checkpoints for Agent State
class Checkpoint(Base):
    """
    Stores intermediate state of the RAG agent for a user.
    Useful for resuming conversations or context between requests.
    """
    __tablename__ = "rag_checkpoints"

    user_id = Column(String, primary_key=True)  # Each user has one checkpoint
    state = Column(JSON)  # Stores the agent's state as JSON
    updated_at = Column(DateTime, default=datetime.utcnow)  # Auto-timestamp



# DB Initialization Helper
def init_db():
    """
    Create all tables defined above if they don’t exist already.
    Call this once at app startup.
    """
    Base.metadata.create_all(bind=engine)
