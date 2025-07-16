# app/services/postgres_storage.py

from app.services.db import SessionLocal, ConversationTurn, Checkpoint
from datetime import datetime
import json

def save_turn(user_id: str, role: str, content):
    from datetime import datetime
    db = SessionLocal()

    # Extract output if content is a dict
    if isinstance(content, dict):
        content = content.get("output", str(content))  # fallback to full dict string

    turn = ConversationTurn(
        user_id=str(user_id),
        role=role,
        content=content,
        timestamp=datetime.utcnow()
    )
    db.add(turn)
    db.commit()
    db.close()



def get_history(user_id: str, limit: int = 5):
    db = SessionLocal()
    turns = db.query(ConversationTurn).filter_by(user_id=user_id).order_by(ConversationTurn.timestamp.desc()).limit(limit).all()
    db.close()
    return list(reversed([{"role": t.role, "content": t.content} for t in turns]))


def save_checkpoint(user_id: str, state: dict):
    db = SessionLocal()
    existing = db.query(Checkpoint).filter_by(user_id=user_id).first()
    if existing:
        existing.state = state
        existing.updated_at = datetime.utcnow()
    else:
        new_cp = Checkpoint(user_id=user_id, state=state)
        db.add(new_cp)
    db.commit()
    db.close()


def load_checkpoint(user_id: str) -> dict:
    db = SessionLocal()
    cp = db.query(Checkpoint).filter_by(user_id=user_id).first()
    db.close()
    return cp.state if cp else None


def reset_checkpoint(user_id: str):
    db = SessionLocal()
    cp = db.query(Checkpoint).filter_by(id=user_id).first()
    if cp:
        db.delete(cp)
        db.commit()
    db.close()
