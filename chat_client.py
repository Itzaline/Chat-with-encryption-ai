import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from cryptography.fernet import Fernet

SERVER_IP = 'localhost'
PORT = 25564


class SecureChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Chat (Fernet)")

        self.nickname = simpledialog.askstring("Никнейм", "Введите ваш ник:", parent=root)
        if not self.nickname:
            root.destroy()
            return

        self.setup_ui()
        self.connect_to_server()

    def setup_ui(self):
        self.text_area = scrolledtext.ScrolledText(self.root, state='disabled')
        self.text_area.pack(padx=10, pady=10, fill='both', expand=True)

        self.entry = tk.Entry(self.root)
        self.entry.pack(padx=10, fill='x')
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = tk.Button(self.root, text="Отправить", command=self.send_message)
        self.send_btn.pack(pady=(0, 10))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_IP, PORT))

            # Получаем ключ от сервера
            self.fernet = Fernet(self.sock.recv(44))  # 44 байта - длина ключа Fernet

            # Отправляем зашифрованный никнейм
            self.sock.send(self.fernet.encrypt(self.nickname.encode()))

            # Поток для приема сообщений
            threading.Thread(target=self.receive_messages, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
            self.root.destroy()

    def send_message(self):
        message = self.entry.get()
        if message:
            try:
                # Шифруем и отправляем сообщение
                full_msg = f"{self.nickname}: {message}"
                encrypted = self.fernet.encrypt(full_msg.encode())
                self.sock.send(encrypted)

                # Немедленно отображаем свое сообщение
                self.display_message(full_msg)
                self.entry.delete(0, tk.END)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка отправки: {e}")

    def receive_messages(self):
        while True:
            try:
                encrypted = self.sock.recv(4096)
                if not encrypted:
                    break

                # Получаем и отображаем сообщения от других
                message = self.fernet.decrypt(encrypted).decode()
                if not message.startswith(self.nickname + ":"):  # Не дублируем свои сообщения
                    self.display_message(message)

            except Exception as e:
                print(f"[Ошибка получения] {e}")
                break

    def display_message(self, msg):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, msg + "\n")
        self.text_area.configure(state='disabled')
        self.text_area.yview(tk.END)

    def on_close(self):
        self.sock.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SecureChatClient(root)
    root.mainloop()