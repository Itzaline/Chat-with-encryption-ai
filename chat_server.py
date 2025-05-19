# chat_server.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import socket
import threading
from cryptography.fernet import Fernet
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pickle

# Инициализация NLP
nltk.download('punkt')
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Загрузка модели
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

with open('vectorizer.pkl', 'rb') as f:
    vectorizer = pickle.load(f)

KEY = Fernet.generate_key()
fernet = Fernet(KEY)

HOST = '0.0.0.0'
PORT = 25564

clients = []
nicknames = []

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = word_tokenize(text)
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

def broadcast(encrypted_msg, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.send(encrypted_msg)
            except:
                clients.remove(client)

def handle_client(client):
    while True:
        try:
            encrypted = client.recv(4096)
            if not encrypted:
                break

            message = fernet.decrypt(encrypted).decode()
            is_spam = False

            if ": " in message:
                _, msg_text = message.split(": ", 1)
                cleaned = preprocess_text(msg_text)
                vectorized = vectorizer.transform([cleaned])
                if model.predict(vectorized)[0] == 1:
                    is_spam = True
                    client.send(fernet.encrypt("Система: Сообщение заблокировано как спам!".encode()))

            if not is_spam:
                broadcast(fernet.encrypt(message.encode()), client)

        except Exception as e:
            print(f"Ошибка: {e}")
            index = clients.index(client)
            clients.remove(client)
            nickname = nicknames.pop(index)
            broadcast(fernet.encrypt(f"{nickname} покинул чат".encode()))
            client.close()
            break

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[Сервер запущен] {HOST}:{PORT}")

    while True:
        client, addr = server.accept()
        client.send(KEY)

        try:
            nickname = fernet.decrypt(client.recv(1024)).decode()
            nicknames.append(nickname)
            clients.append(client)

            print(f"Подключился: {nickname}")
            broadcast(fernet.encrypt(f"{nickname} присоединился!".encode()))
            client.send(fernet.encrypt("Добро пожаловать!".encode()))

            threading.Thread(target=handle_client, args=(client,)).start()
        except:
            client.close()

if __name__ == "__main__":
    
    start_server()