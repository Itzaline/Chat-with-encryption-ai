from sqlalchemy.orm import Session
from . import models

def create_user(
    db: Session,
    username: str,
    display_name: str,
    password_hash: str,
    avatar_url: str = None
) -> models.User:
    db_user = models.User(
        username=username,
        display_name=display_name,
        password_hash=password_hash,
        avatar_url=avatar_url
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user