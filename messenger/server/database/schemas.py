from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    display_name: str

class UserCreate(UserBase):
    password: str
    public_key: str

class User(UserBase):
    id: int
    avatar_url: str
    
    class Config:
        from_attributes = True  # Замените orm_mode на это