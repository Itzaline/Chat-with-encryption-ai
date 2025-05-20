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
        self.clients = {}  # {client_socket: {'nickname': str, 'address': tuple}}
        self.antispam = AntiSpamSystem()
        self.lock = threading.Lock()

    def broadcast(self, message, sender=None, is_system=False):
        """Рассылка сообщений всем клиентам"""
        with self.lock:
            for client in list(self.clients.keys()):
                try:
                    if client != sender:
                        if is_system:
                            msg = f"!SYSTEM!{message}"
                        else:
                            msg = message
                        client.send(self.fernet.encrypt(msg.encode()))
                except:
                    self.remove_client(client)

    def send_user_list(self, client):
        """Отправка списка пользователей конкретному клиенту"""
        with self.lock:
            user_list = "USERLIST:" + ",".join([info['nickname'] for info in self.clients.values()])
            client.send(self.fernet.encrypt(user_list.encode()))

    def remove_client(self, client):
        """Удаление отключившегося клиента"""
        with self.lock:
            if client in self.clients:
                nickname = self.clients[client]['nickname']
                del self.clients[client]
                client.close()

                # Уведомляем о выходе пользователя
                self.broadcast(f"{nickname} покинул чат", is_system=True)

                # Обновляем списки пользователей у всех
                self.update_all_user_lists()

    def update_all_user_lists(self):
        """Обновление списков пользователей у всех клиентов"""
        with self.lock:
            user_list = "USERLIST:" + ",".join([info['nickname'] for info in self.clients.values()])
            for client in list(self.clients.keys()):
                try:
                    client.send(self.fernet.encrypt(user_list.encode()))
                except:
                    self.remove_client(client)

    def handle_private_message(self, sender_nickname, recipient_nickname, message):
        """Обработка личных сообщений"""
        with self.lock:
            for client, info in self.clients.items():
                if info['nickname'] == recipient_nickname:
                    try:
                        msg = f"!PRIVATE!{sender_nickname}:{message}"
                        client.send(self.fernet.encrypt(msg.encode()))
                        return True
                    except:
                        self.remove_client(client)
        return False

    def handle_client(self, client, address):
        """Обработка подключения клиента"""
        nickname = None
        try:
            # Получаем и устанавливаем никнейм
            encrypted_nick = client.recv(1024)
            nickname = self.fernet.decrypt(encrypted_nick).decode()

            with self.lock:
                self.clients[client] = {'nickname': nickname, 'address': address}

            # Уведомляем о новом пользователе
            self.broadcast(f"{nickname} присоединился к чату", is_system=True)

            # Отправляем список пользователей новому клиенту
            self.send_user_list(client)

            # Обновляем списки у всех клиентов
            self.update_all_user_lists()

            while True:
                encrypted = client.recv(4096)
                if not encrypted:
                    break

                message = self.fernet.decrypt(encrypted).decode()

                # Обработка команд
                if message.startswith("/"):
                    if message.startswith("/getusers"):
                        self.send_user_list(client)
                    elif message.startswith("/private "):
                        parts = message[len("/private "):].split(" ", 1)
                        if len(parts) == 2:
                            recipient, private_msg = parts
                            if self.antispam.is_spam(private_msg):
                                client.send(self.fernet.encrypt(
                                    "!SYSTEM!Ваше сообщение заблокировано из-за спама!".encode()
                                ))
                            else:
                                if not self.handle_private_message(nickname, recipient, private_msg):
                                    client.send(self.fernet.encrypt(
                                        f"!SYSTEM!Пользователь {recipient} не найден".encode()
                                    ))
                    continue

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
            client, address = server.accept()
            try:
                # Отправляем ключ шифрования новому клиенту
                client.send(self.key)
                # Запускаем обработчик клиента в отдельном потоке
                threading.Thread(
                    target=self.handle_client,
                    args=(client, address),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"Ошибка подключения: {e}")
                client.close()


if __name__ == "__main__":
    server = ChatServer()
    server.start()