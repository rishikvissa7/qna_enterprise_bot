# app/services/postgres_storage.py

# Import models and session from the database setup
from app.db.db import SessionLocal, ConversationTurn, Checkpoint
from datetime import datetime


# Save a Single Turn (User or Assistant)
def save_turn(user_id: str, role: str, content):
    """
    Save one message turn in the conversation (either user or assistant).

    Parameters:
    - user_id: Unique ID of the user
    - role: Either 'user' or 'assistant'
    - content: Text or dictionary response to save
    """
    db = SessionLocal()

    # If the content is a dict (like from a tool), try extracting the actual message
    if isinstance(content, dict):
        content = content.get("output", str(content))  # fallback to string version

    # Create a new ConversationTurn row
    turn = ConversationTurn(
        user_id=str(user_id),
        role=role,
        content=content,
        timestamp=datetime.utcnow()
    )

    db.add(turn)
    db.commit()
    db.close()


# Retrieve Recent Conversation History
def get_history(user_id: str, limit: int = 5):
    """
    Get the last `limit` conversation turns for a user.

    Returns:
    - List of dictionaries like: [{role: 'user', content: '...'}, ...]
    """
    db = SessionLocal()

    # Fetch recent turns in reverse order (newest first)
    turns = (
        db.query(ConversationTurn)
        .filter_by(user_id=user_id)
        .order_by(ConversationTurn.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    db.close()

    # Reverse to show oldest first (natural conversation flow)
    return list(reversed([
        {"role": t.role, "content": t.content} for t in turns
    ]))


# Save or Update Agent Checkpoint

def save_checkpoint(user_id: str, state: dict):
    """
    Save or update the current agent state for a user.
    Useful for restoring the same context later.
    """
    db = SessionLocal()
    
    existing = db.query(Checkpoint).filter_by(user_id=user_id).first()

    if existing:
        # Update existing state
        existing.state = state
        existing.updated_at = datetime.utcnow()
    else:
        # Create new checkpoint entry
        new_cp = Checkpoint(user_id=user_id, state=state)
        db.add(new_cp)

    db.commit()
    db.close()



# Load Agent Checkpoint for a User

def load_checkpoint(user_id: str) -> dict:
    """
    Load the last saved agent state for the user.

    Returns:
    - A dictionary representing the state or None if no checkpoint exists.
    """
    db = SessionLocal()
    cp = db.query(Checkpoint).filter_by(user_id=user_id).first()
    db.close()
    return cp.state if cp else None


# Reset (Delete) Checkpoint for a User

def reset_checkpoint(user_id: str):
    """
    Delete the checkpoint state for a user (if any exists).
    """
    db = SessionLocal()
    
    # NOTE: This should filter by user_id, not id.
    cp = db.query(Checkpoint).filter_by(user_id=user_id).first()

    if cp:
        db.delete(cp)
        db.commit()

    db.close()
