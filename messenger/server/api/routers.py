from fastapi import APIRouter, UploadFile, File
from database import crud
from database.schemas import UserCreate  # Исправлен импорт
from database.models import User
from security import get_password_hash



router = APIRouter()

@router.post("/register")
async def register_user(user: UserCreate, avatar: UploadFile = File(...)):
    avatar_url = f"avatars/{user.username}.png"
    with open(avatar_url, "wb") as f:
        f.write(await avatar.read())
    
    return crud.create_user(
        username=user.username,
        display_name=user.display_name,
        avatar_url=avatar_url,
        public_key=user.public_key
    )
    
@router.post("/register")
async def register_user(user: UserCreate, avatar: UploadFile = File(...)):
    hashed_password = get_password_hash(user.password)
    # Сохраняем hashed_password вместо user.password
