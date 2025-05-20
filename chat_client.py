import socket
import threading
from cryptography.fernet import Fernet
import json
import os
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict
import pickle
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

nltk.download(['punkt', 'stopwords'], quiet=True)

class AntiSpamSystem:
    def __init__(self):
        self.stop_words = set(stopwords.words('english') + ['ur', 'nbsp', 'lt', 'gt'])
        self.load_artifacts()

    def load_artifacts(self):

        with open('model.pkl', 'rb') as f:
            self.model = pickle.load(f)
        with open('vectorizer.pkl', 'rb') as f:
            self.vectorizer = pickle.load(f)

    def preprocess(self, text):
        text = text.lower()
        text = ''.join([char if char.isalpha() else ' ' for char in text])
        words = word_tokenize(text)
        return ' '.join([w for w in words if w not in self.stop_words and len(w) > 2])

    def is_spam(self, message):
        cleaned = self.preprocess(message)
        if not cleaned:
            return False
        vectorized = self.vectorizer.transform([cleaned])
        return self.model.predict(vectorized)[0] == 1


class RateLimiter:
    def __init__(self, max_messages=4, period=1):
        self.max_messages = max_messages  # Максимум сообщений
        self.period = period              # Временной период (в секундах)
        self.timestamps = defaultdict(list)  # Хранение временных меток по IP

    def check_limit(self, address):
        now = datetime.now()
        ip, port = address

        # Убираем старые записи
        self.timestamps[address] = [
            t for t in self.timestamps[address]
            if now - t < timedelta(seconds=self.period)
        ]

        return len(self.timestamps[address]) < self.max_messages

    def add_request(self, address):
        self.timestamps[address].append(datetime.now())


# ================== ОСНОВНОЙ СЕРВЕР ==================

class ChatServer:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        self.host = '0.0.0.0'
        self.port = 25564
        self.clients = {}  # {socket: {'nickname': str}}
        self.USERS_FILE = 'users.json'
        self.users_db = self.load_users()
        self.lock = threading.Lock()

        # Инициализация спам-фильтра и лимитера
        self.antispam = AntiSpamSystem()
        self.rate_limiter = RateLimiter(max_messages=4, period=1)

    def load_users(self):
        if os.path.exists(self.USERS_FILE):
            with open(self.USERS_FILE, 'r') as f:
                return json.load(f)

        return {}

    def save_users(self):
        with open(self.USERS_FILE, 'w') as f:
            json.dump(self.users_db, f, indent=2)

    def broadcast(self, message, sender=None, is_system=False):
        with self.lock:
            for client in list(self.clients.keys()):
                if client != sender:
                    msg = f"!SYSTEM!{message}" if is_system else message
                    client.send(self.fernet.encrypt(msg.encode()))

    def send_user_list(self, client):
        user_list = "USERLIST:" + ",".join([info['nickname'] for info in self.clients.values()])
        client.send(self.fernet.encrypt(user_list.encode()))

    def remove_client(self, client):
        if client in self.clients:
            nickname = self.clients[client]['nickname']
            del self.clients[client]
            client.close()

            self.broadcast(f"{nickname} покинул чат", is_system=True)
            self.update_all_user_lists()

    def update_all_user_lists(self):
        user_list = "USERLIST:" + ",".join([info['nickname'] for info in self.clients.values()])
        for client in list(self.clients.keys()):
            client.send(self.fernet.encrypt(user_list.encode()))

    def handle_private_message(self, sender_nickname, recipient_nickname, message):
        for client, info in self.clients.items():
            if info['nickname'] == recipient_nickname:
                msg = f"!PRIVATE!{sender_nickname}:{message}"
                client.send(self.fernet.encrypt(msg.encode()))
                return True

        return False

    def handle_client(self, client, address):
        nickname = None
        encrypted_nick = client.recv(1024)
        nickname = self.fernet.decrypt(encrypted_nick).decode()
        # Проверяем, зарегистрирован ли пользователь
        if nickname.startswith("REGISTER:"):
            _, login, pwd_hash = nickname.split(":", 2)
            if login in self.users_db:
                client.send(self.fernet.encrypt("REGISTER_FAILED_EXISTS".encode()))
                return
            self.users_db[login] = pwd_hash
            self.save_users()
            client.send(self.fernet.encrypt("REGISTER_SUCCESS".encode()))
            nickname = login
        elif nickname.startswith("LOGIN:"):
            login = nickname.split(":", 1)[1]
            client.send(self.fernet.encrypt("AUTH_REQUIRED".encode()))
            if login in self.users_db:
                client.send(self.fernet.encrypt("AUTH_REQUIRED".encode()))
                pwd_hash_data = client.recv(1024)
                pwd_hash = self.fernet.decrypt(pwd_hash_data).decode()
                if pwd_hash == self.users_db[login]:
                    client.send(self.fernet.encrypt("AUTH_SUCCESS".encode()))
                    nickname = login
                else:
                    client.send(self.fernet.encrypt("AUTH_FAILED".encode()))
                    return
        else:
            # Совместимость со старым клиентом
            pass
        with self.lock:
            self.clients[client] = {'nickname': nickname}
        self.broadcast(f"{nickname} присоединился к чату", is_system=True)
        self.send_user_list(client)
        self.update_all_user_lists()
        while True:
            encrypted = client.recv(4096)
            if not encrypted:
                break
            try:
                message = self.fernet.decrypt(encrypted).decode()
            except Exception as e:
                print(f"[Ошибка расшифрования] {e}")
                continue
            # Проверка на флуд (лимит сообщений)
            if not self.rate_limiter.check_limit(address):
                try:
                    client.send(self.fernet.encrypt(
                        "!SYSTEM!Слишком много сообщений. Подождите.".encode()
                    ))
                except:
                    break
                continue
            self.rate_limiter.add_request(address)
            # Обработка команд
            if message.startswith("/private "):
                parts = message[len("/private "):].split(" ", 1)
                if len(parts) == 2:
                    recipient, private_msg = parts
                    if not self.handle_private_message(nickname, recipient, private_msg):
                        client.send(self.fernet.encrypt(
                            f"!SYSTEM!Пользователь {recipient} не найден".encode()
                        ))
                continue
            if message.startswith("/getusers"):
                self.send_user_list(client)
                continue
            if message.startswith("/quit"):
                break
            # Проверка на спам
            if self.antispam.is_spam(message):
                client.send(self.fernet.encrypt(
                    "!SYSTEM!Ваше сообщение заблокировано из-за спама!".encode()
                ))
                self.broadcast(
                    f"Сообщение от {nickname} заблокировано системой анти-спама",
                    is_system=True
                )
                continue
            # Отправка обычного сообщения
            self.broadcast(f"{nickname}: {message}", client)

            self.remove_client(client)

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()
        print(f"[Сервер запущен] {self.host}:{self.port}")

        while True:
            client, addr = server.accept()
            client.send(self.key)
            threading.Thread(
                target=self.handle_client,
                args=(client, addr),
                daemon=True
            ).start()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
