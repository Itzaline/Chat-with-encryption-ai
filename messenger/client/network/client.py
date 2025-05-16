import websockets
import json
import asyncio
from shared.protocols import MessageProtocol  # Добавлен импорт
from config import Config
import aiohttp
import json
from shared.protocols import UserCreate, UserLogin

class NetworkClient:
    def __init__(self, crypto_manager):  # Добавляем параметр в конструктор
        self.base_url = "http://localhost:8000"
        self.crypto = crypto_manager  # Сохраняем ссылку на крипто-менеджер
    
    async def login(self, username: str, password: str):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/login",
                json=UserLogin(username=username, password=password).dict()
            ) as response:
                if response.status == 200:
                    return await response.json()
                raise Exception(await response.text())
    
    async def register(self, user_data: dict):
        async with aiohttp.ClientSession() as session:
            # Отправка аватарки через FormData
            data = aiohttp.FormData()
            data.add_field('user', 
                          json.dumps({
                              "username": user_data['username'],
                              "display_name": user_data['display_name'],
                              "password": user_data['password']
                          }), 
                          content_type='application/json')
            
            if 'avatar' in user_data and user_data['avatar']:
                data.add_field('avatar',
                              open(user_data['avatar'], 'rb'),
                              filename='avatar.png',
                              content_type='image/png')
            
            async with session.post(
                f"{self.base_url}/register",
                data=data
            ) as response:
                if response.status == 200:
                    return await response.json()
                raise Exception(await response.text())

class NetworkClient:
    def __init__(self, crypto_manager):
        self.crypto = crypto_manager
        self.server_url = Config.SERVER_URL
        
    async def send_message(self, receiver: str, message: str, sender_info: dict):
        async with websockets.connect(f"ws://{self.server_url}/ws") as ws:  # Требует установки websockets
            encrypted = self.crypto.encrypt(message)
            msg = MessageProtocol(
                sender=sender_info['username'],
                sender_display=sender_info['display_name'],
                avatar_url=sender_info['avatar'],
                encrypted_data=encrypted.decode(),
                timestamp=asyncio.get_event_loop().time()  # Импорт asyncio
            )
            await ws.send(json.dumps(msg.dict()))  # Требует импорта json
    
    async def login_user(self, username: str, password: str):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.server_url}/login",
                json={"username": username, "password": password}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.json()
                    raise Exception(error.get("detail", "Login failed"))
            
