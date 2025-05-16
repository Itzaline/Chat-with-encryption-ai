from pydantic import BaseModel

class MessageProtocol(BaseModel):
    sender: str
    sender_display: str
    avatar_url: str
    encrypted_data: str
    timestamp: float

class UserCreate(BaseModel):
    username: str
    display_name: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str