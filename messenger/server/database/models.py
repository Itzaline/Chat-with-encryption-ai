from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    display_name = Column(String(50))
    avatar_url = Column(String(200))
    public_key = Column(String(500))