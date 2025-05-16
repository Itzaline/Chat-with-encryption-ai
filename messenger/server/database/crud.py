from sqlalchemy.orm import Session
from . import models

def get_user(db: Session, username: str):
    return db.query(models.User).filter(
        models.User.username == username
    ).first()

def search_users(db: Session, username: str):
    return db.query(models.User).filter(
        models.User.username.ilike(f"%{username}%")
    ).limit(20).all()