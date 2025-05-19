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
        try:
            index = self.clients.index(client)
            nickname = self.nicknames.pop(index)
            self.clients.remove(client)
            self.broadcast(self.fernet.encrypt(f"{nickname} покинул чат".encode()))
            client.close()
        except ValueError:
            pass

    def handle_client(self, client):
        nickname = None
        try:
            encrypted_nick = client.recv(1024)
            nickname = self.fernet.decrypt(encrypted_nick).decode()
        
            self.clients.append(client)
            self.broadcast(self.fernet.encrypt(f"{nickname} присоединился!".encode()))

            while True:
                encrypted = client.recv(4096)
                if not encrypted:
                    break

                message = self.fernet.decrypt(encrypted).decode()
            
                if self.antispam.is_spam(message):
                    # Уведомление отправителю
                    sender_notification = "Система: Ваше сообщение заблокировано из-за спама!"
                    client.send(self.fernet.encrypt(sender_notification.encode()))
                
                    # Уведомление всем участникам
                    global_notification = f"Система: Сообщение от {nickname} заблокировано!"
                    self.broadcast(self.fernet.encrypt(global_notification.encode()))
                    continue

                # Рассылка обычного сообщения
                self.broadcast(self.fernet.encrypt(f"{nickname}: {message}".encode()), client)

        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            self.remove_client(client)

    def start(self):
        """Запуск сервера"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()
        print(f"[Сервер запущен] {self.host}:{self.port}")

        while True:
            client, addr = server.accept()
            try:
                client.send(self.key)
                threading.Thread(target=self.handle_client, args=(client,)).start()
            except Exception as e:
                print(f"Ошибка подключения: {e}")
                client.close()
                
    def is_spam(self, message):
        """Проверка на спам с дополнительными правилами"""
        # Проверка по модели ML
        ml_result = self.ml_check(message)
    
        # Дополнительные правила
        rule_based_result = self.rule_based_check(message)
    
        return ml_result or rule_based_result

    def ml_check(self, message):
        cleaned = self.preprocess(message)
        vectorized = self.vectorizer.transform([cleaned])
        return self.model.predict(vectorized)[0] == 1

    def rule_based_check(self, message):
        """Ручные правила для распространенных спам-паттернов"""
        spam_patterns = [
            r'\b(?:win|won|prize|reward|free|claim)\b',
            r'\b\d+\s*(?:USD|EUR|руб|р)\b',
            r'\b(?:urgent|limited|offer)\b'
        ]
    
        for pattern in spam_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False

if __name__ == "__main__":
    server = ChatServer()
    server.start()