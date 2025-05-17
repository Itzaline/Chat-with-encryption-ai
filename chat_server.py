import socket
import threading
from cryptography.fernet import Fernet

# Генерация ключа (должен быть одинаковый на сервере и клиенте)
KEY = Fernet.generate_key()
fernet = Fernet(KEY)

HOST = '0.0.0.0'
PORT = 25564

clients = []
nicknames = []


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
            encrypted = client.recv(1024)
            if not encrypted:
                break

            # Добавьте лог для отладки:
            print(f"Получено зашифрованное сообщение: {encrypted}")

            message = fernet.decrypt(encrypted).decode()
            print(f"Расшифрованное сообщение: {message}")

            encrypted_msg = fernet.encrypt(f"{message}".encode())
            broadcast(encrypted_msg, client)

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
    server.bind((HOST, PORT))
    server.listen()
    print(f"[Сервер запущен] {HOST}:{PORT}")
    print(f"Ключ шифрования: {KEY.decode()}")

    while True:
        client, address = server.accept()

        # Отправляем ключ новому клиенту (в реальном приложении нужно защищенное соединение!)
        client.send(KEY)

        nickname = fernet.decrypt(client.recv(1024)).decode()
        nicknames.append(nickname)
        clients.append(client)

        print(f"Подключился: {nickname}")
        broadcast(fernet.encrypt(f"{nickname} присоединился!".encode()))
        client.send(fernet.encrypt("Добро пожаловать!".encode()))

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()


if __name__ == "__main__":
    start_server()