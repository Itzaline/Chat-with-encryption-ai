from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    display_name: str

class UserCreate(BaseModel):
    username: str
    display_name: str
    password: str

class User(UserBase):
    id: int
    avatar_url: str
    
    class Config:
        from_attributes = True  # Замените orm_mode на это
        
class UserLogin(BaseModel):
    username: str
    password: str