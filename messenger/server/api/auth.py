from fastapi import APIRouter, HTTPException, UploadFile, File, Form  # Добавлен Form
from pydantic import BaseModel
from security import verify_password, get_password_hash
from database.schemas import UserLogin, UserCreate
from server.database import crud  # Абсолютный импорт

router = APIRouter()

@router.post("/register")
async def register(
    username: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
    avatar: UploadFile = File(None)
):
    # Хеширование пароля
    hashed_password = get_password_hash(password)
    
    # Сохранение аватарки
    avatar_url = None
    if avatar:
        avatar_url = f"avatars/{username}.{avatar.filename.split('.')[-1]}"
        with open(avatar_url, "wb") as f:
            f.write(await avatar.read())
    
    # Создание пользователя
    db_user = crud.create_user(
        username=username,
        display_name=display_name,
        password_hash=hashed_password,
        avatar_url=avatar_url
    )
    
    return {
        "user": {
            "username": db_user.username,
            "display_name": db_user.display_name,
            "avatar": db_user.avatar_url
        }
    }