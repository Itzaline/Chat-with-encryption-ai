import websockets
import json
import asyncio
from shared.protocols import MessageProtocol  # Добавлен импорт
from config import Config

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