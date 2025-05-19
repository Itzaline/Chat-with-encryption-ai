from email import message
import socket
import threading
from cryptography.fernet import Fernet
import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from datetime import datetime

# Инициализация NLP
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

class AntiSpamSystem:
    def __init__(self):
        self.load_artifacts()
        self.spam_count = {}
        
    def load_artifacts(self):
        """Загрузка модели и векторайзера"""
        try:
            with open('model.pkl', 'rb') as f:
                self.model = pickle.load(f)
            with open('vectorizer.pkl', 'rb') as f:
                self.vectorizer = pickle.load(f)
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            exit(1)

    def preprocess(self, text):
        """Очистка текста"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        words = word_tokenize(text)
        words = [w for w in words if w not in stop_words]
        return ' '.join(words)

    def is_spam(self, message):
        """Проверка на спам"""
        try:
            cleaned = self.preprocess(message)
            vectorized = self.vectorizer.transform([cleaned])
            return self.model.predict(vectorized)[0] == 1
        except Exception as e:
            print(f"Ошибка проверки спама: {e}")
            return False

class ChatServer:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        self.host = '0.0.0.0'
        self.port = 25564
        self.clients = []
        self.nicknames = []
        self.antispam = AntiSpamSystem()

    def broadcast(self, encrypted_msg, sender=None):
        """Рассылка сообщений"""
        for client in self.clients:
            if client != sender:
                try:
                    client.send(encrypted_msg)
                except:
                    self.remove_client(client)

    def remove_client(self, client):
        """Удаление отключившегося клиента"""
        index = self.clients.index(client)
        nickname = self.nicknames.pop(index)
        self.clients.remove(client)
        self.broadcast(self.fernet.encrypt(f"{nickname} покинул чат".encode()))
        client.close()

    def handle_client(self, client):
        """Обработка сообщений от клиента"""
        nickname = ""
        while True:
            try:
                encrypted = client.recv(4096)
                if not encrypted:
                    break

                essage = self.fernet.decrypt(encrypted).decode()
            
                # Первое сообщение - никнейм
                if not nickname:
                    nickname = message
                    self.nicknames.append(nickname)
                    self.broadcast(self.fernet.encrypt(f"{nickname} присоединился!".encode()))
                    continue

                # Проверка на спам
                if self.antispam.is_spam(message):
                    # Логирование и блокировка
                    print(f"[{datetime.now()}] СПАМ от {nickname}: {message}")
                    spam_notification = self.fernet.encrypt(
                        "Система: Ваше сообщение было заблокировано как спам!".encode()
                    )
                    client.send(spam_notification)
                    continue

                # Рассылка нормального сообщения
                full_msg = f"{nickname}: {message}"
                self.broadcast(self.fernet.encrypt(full_msg.encode()), sender=client)

            except Exception as e:
                print(f"Ошибка: {e}")
                self.remove_client(client, nickname)
                break

    def start(self):
        """Запуск сервера"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()
        print(f"[Сервер запущен] {self.host}:{self.port}")

        while True:
            client, addr = server.accept()
            client.send(self.key)

            try:
                nickname = self.fernet.decrypt(client.recv(1024)).decode()
                self.nicknames.append(nickname)
                self.clients.append(client)

                print(f"Подключился: {nickname}")
                self.broadcast(self.fernet.encrypt(f"{nickname} присоединился!".encode()))
                client.send(self.fernet.encrypt("Добро пожаловать!".encode()))

                threading.Thread(target=self.handle_client, args=(client,)).start()
            except Exception as e:
                print(f"Ошибка подключения: {e}")
                client.close()

if __name__ == "__main__":
    server = ChatServer()
    server.start()