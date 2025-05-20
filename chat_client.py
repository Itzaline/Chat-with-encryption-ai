import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk, Listbox, Entry, Toplevel
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from datetime import datetime
import json
import base64
import os
import hashlib

SERVER_IP = 'localhost'
PORT = 25564


class PrivateChatWindow:
    def __init__(self, root, nickname, recipient, fernet, sock, client, password):
        self.root = root
        self.nickname = nickname
        self.recipient = recipient
        self.fernet = fernet
        self.sock = sock
        self.client = client
        self.is_closed = False

        # Генерация ключа для шифрования истории
        salt = b'hashpassw'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet_history = Fernet(derived_key)

        self.window = Toplevel(root)
        self.window.title(f"Личный чат с {recipient}")
        self.window.geometry("600x500")

        self.text_area = scrolledtext.ScrolledText(
            self.window, state='disabled', wrap=tk.WORD, font=("Helvetica", 11), bg='white')
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.tag_config('self', foreground='#2d572c')
        self.text_area.tag_config('other', foreground='#8a2be2')

        input_frame = ttk.Frame(self.window)
        input_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        self.entry = Entry(input_frame, font=("Helvetica", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", lambda e: self.send_message())

        send_btn = ttk.Button(input_frame, text="Отправить", command=self.send_message)
        send_btn.pack(side=tk.RIGHT)

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.load_private_messages()
        self.entry.focus_set()

    def get_chat_filename(self):
        return f"{self.nickname}_{self.recipient}.json"

    def save_private_message(self, timestamp, sender, message, tag):
        if self.is_closed:
            return
        filename = self.get_chat_filename()
        try:
            messages = []
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    encrypted_data = f.read()
                if encrypted_data:
                    decrypted_data = self.fernet_history.decrypt(encrypted_data)
                    messages = json.loads(decrypted_data.decode())
            messages.append({
                "timestamp": timestamp,
                "sender": sender,
                "message": message,
                "tag": tag
            })
            with open(filename, 'wb') as f:
                encrypted = self.fernet_history.encrypt(json.dumps(messages, ensure_ascii=False, indent=2).encode())
                f.write(encrypted)
        except Exception as e:
            print(f"[Ошибка] Сохранение сообщения: {e}")

    def load_private_messages(self):
        filename = self.get_chat_filename()
        try:
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.fernet_history.decrypt(encrypted_data)
                messages = json.loads(decrypted_data.decode())
                for msg in messages:
                    formatted_msg = f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}"
                    self.display_message(formatted_msg, msg['tag'])
        except Exception as e:
            print(f"[Ошибка] Загрузка истории: {e}")

    def send_message(self):
        message = self.entry.get().strip()
        if message and not self.is_closed:
            try:
                cmd = f"/private {self.recipient} {message}"
                encrypted = self.fernet.encrypt(cmd.encode())
                self.sock.send(encrypted)

                timestamp = datetime.now().strftime("%H:%M")
                formatted_msg = f"[{timestamp}] Вы: {message}"
                self.display_message(formatted_msg, 'self')
                self.save_private_message(timestamp, "Вы", message, 'self')
                self.entry.delete(0, tk.END)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось отправить сообщение: {e}")

    def display_message(self, msg, tag='other'):
        if not self.is_closed and self.window.winfo_exists():
            try:
                self.text_area.configure(state='normal')
                self.text_area.insert(tk.END, msg + "\n", tag)
                self.text_area.configure(state='disabled')
                self.text_area.see(tk.END)
            except tk.TclError:
                pass

    def on_close(self):
        self.is_closed = True
        try:
            self.window.destroy()
            if self.recipient in self.client.private_chats:
                del self.client.private_chats[self.recipient]
        except tk.TclError:
            pass


class SecureChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Gammagram")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        self.setup_styles()
        self.nickname = None
        self.password = None
        self.fernet = None
        self.fernet_history = None
        self.sock = None
        self.connected = False
        self.private_chats = {}
        self.online_users = []

        self.setup_ui()
        self.connect_to_server()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', padding=6, relief='flat', background='#4a7a8c')
        self.style.configure('TEntry', padding=6)
        self.style.map('TButton',
                       background=[('active', '#5a8a9c'), ('disabled', '#cccccc')])
        self.text_font = ('Helvetica', 11)
        self.alert_font = ('Helvetica', 11, 'bold')
        self.status_font = ('Helvetica', 9)
        self.userlist_font = ('Helvetica', 10)

    def get_login(self):
        login_window = Toplevel(self.root)
        login_window.title("Вход или регистрация")
        login_window.geometry("300x180")
        login_window.resizable(False, False)

        tk.Label(login_window, text="Никнейм:", font=("Helvetica", 11)).pack(pady=(10, 0))
        username_entry = Entry(login_window, font=("Helvetica", 11), width=25)
        username_entry.pack(pady=5)

        tk.Label(login_window, text="Пароль:", font=("Helvetica", 11)).pack()
        password_entry = Entry(login_window, show="*", font=("Helvetica", 11), width=25)
        password_entry.pack(pady=5)

        self.is_registering = False

        def on_login():
            self.nickname = username_entry.get().strip()
            self.password = password_entry.get().strip()
            if self.nickname and self.password:
                login_window.destroy()

        def on_register():
            self.nickname = username_entry.get().strip()
            self.password = password_entry.get().strip()
            if self.nickname and self.password:
                self.is_registering = True
                login_window.destroy()

        btn_frame = ttk.Frame(login_window)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Войти", command=on_login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Зарегистрироваться", command=on_register).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(login_window)

        if not hasattr(self, 'nickname') or not self.nickname or not self.password:
            return None, None, False
        return self.nickname, self.password, getattr(self, 'is_registering', False)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        user_frame = ttk.Frame(main_frame, width=200)
        user_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        search_frame = ttk.Frame(user_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_user_list)
        self.search_entry = Entry(search_frame, textvariable=self.search_var, font=("Helvetica", 10))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="X", width=3, command=self.clear_search).pack(side=tk.RIGHT)

        self.user_list_label = ttk.Label(user_frame, text="Пользователи онлайн:", font=("Helvetica", 10))
        self.user_list_label.pack(pady=(0, 5))

        self.user_listbox = Listbox(user_frame, font=("Helvetica", 10), selectbackground='#4a7a8c', selectforeground='white')
        self.user_listbox.pack(fill=tk.BOTH, expand=True)
        self.user_listbox.bind("<Double-Button-1>", self.start_private_chat)

        ttk.Button(user_frame, text="Обновить список", command=self.request_user_list).pack(fill=tk.X, pady=(5, 0))

        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.chat_title = ttk.Label(chat_frame, text="Общий чат", font=("Helvetica", 11, 'bold'))
        self.chat_title.pack(pady=(0, 5))

        self.text_area = scrolledtext.ScrolledText(chat_frame, state='disabled', wrap=tk.WORD, font=("Helvetica", 11), bg='white')
        self.text_area.pack(fill=tk.BOTH, expand=True)

        self.text_area.tag_config('alert', foreground='red', font=("Helvetica", 11, 'bold'))
        self.text_area.tag_config('system', foreground='blue')
        self.text_area.tag_config('self', foreground='#2d572c')
        self.text_area.tag_config('other', foreground='black')

        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        self.entry = Entry(input_frame, font=("Helvetica", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry.bind("<Return>", lambda e: self.send_message())
        self.entry.bind("<KeyRelease>", self.update_send_button_state)

        self.send_btn = ttk.Button(input_frame, text="Отправить", command=self.send_message, state='disabled')
        self.send_btn.pack(side=tk.RIGHT)

        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        self.status_label = ttk.Label(self.status_frame, text="Подключение...", font=("Helvetica", 9), foreground='#666666')
        self.status_label.pack(side=tk.LEFT)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(30000, self.update_user_list_timer)

    def filter_user_list(self, *args):
        search_term = self.search_var.get().lower()
        self.user_listbox.delete(0, tk.END)
        for user in self.online_users:
            if search_term in user.lower():
                self.user_listbox.insert(tk.END, user)
        if not search_term or not self.user_listbox.size():
            self.user_listbox.delete(0, tk.END)
            for user in self.online_users:
                self.user_listbox.insert(tk.END, user)
            if not self.user_listbox.size():
                self.user_listbox.insert(tk.END, "Ничего не найдено")

    def clear_search(self):
        self.search_var.set("")
        self.search_entry.focus()

    def update_send_button_state(self, event=None):
        if self.entry.get().strip() and self.connected:
            self.send_btn.config(state='normal')
        else:
            self.send_btn.config(state='disabled')

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_IP, PORT))
            key = self.sock.recv(44)
            self.fernet = Fernet(key)

            self.nickname, self.password, is_registering = self.get_login()
            if not self.nickname or not self.password:
                self.root.destroy()
                return

            pwd_hash = hashlib.sha256(self.password.encode()).hexdigest()

            if is_registering:
                self.sock.send(self.fernet.encrypt(f"REGISTER:{self.nickname}:{pwd_hash}".encode()))
                response = self.sock.recv(1024)
                result = self.fernet.decrypt(response).decode()
                if result == "REGISTER_SUCCESS":
                    messagebox.showinfo("Успех", "Вы успешно зарегистрировались!")
                elif result == "REGISTER_FAILED_EXISTS":
                    messagebox.showerror("Ошибка", "Пользователь уже существует")
                    self.root.destroy()
                    return
                else:
                    messagebox.showerror("Ошибка", "Не удалось зарегистрироваться")
                    self.root.destroy()
                    return
            else:
                self.sock.send(self.fernet.encrypt(f"LOGIN:{self.nickname}".encode()))
                response = self.sock.recv(1024)
                result = self.fernet.decrypt(response).decode()
                if result == "AUTH_REQUIRED":
                    self.sock.send(self.fernet.encrypt(pwd_hash.encode()))
                    auth_result = self.sock.recv(1024)
                    auth_result = self.fernet.decrypt(auth_result).decode()
                    if auth_result != "AUTH_SUCCESS":
                        messagebox.showerror("Ошибка", "Неверный логин или пароль")
                        self.root.destroy()
                        return

            self.connected = True
            self.update_status("Подключено", "#2d572c")
            self.update_send_button_state()
            self.request_user_list()

            # Генерация ключа для шифрования истории
            salt = b'hashpassw'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
            self.fernet_history = Fernet(derived_key)

            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            self.update_status(f"Ошибка подключения: {e}", "red")
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
            self.root.after(1000, self.root.destroy)

    def update_status(self, text, color="#666666"):
        self.status_label.config(text=text, foreground=color)

    def send_message(self):
        message = self.entry.get().strip()
        if message and self.connected:
            try:
                encrypted = self.fernet.encrypt(message.encode())
                self.sock.send(encrypted)
                timestamp = datetime.now().strftime("%H:%M")
                self.display_message(f"[{timestamp}] Вы: {message}", 'self')
                self.entry.delete(0, tk.END)
                self.update_send_button_state()
            except Exception as e:
                self.update_status(f"Ошибка отправки: {e}", "red")
                messagebox.showerror("Ошибка", f"Ошибка отправки: {e}")
                self.connected = False
                self.update_send_button_state()

    def display_message(self, msg, tag='other'):
        try:
            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, msg + "\n", tag)
            self.text_area.configure(state='disabled')
            self.text_area.yview(tk.END)
        except tk.TclError:
            pass

    def receive_messages(self):
        while True:
            try:
                encrypted = self.sock.recv(4096)
                if not encrypted:
                    break
                message = self.fernet.decrypt(encrypted).decode()
                if message.startswith("USERLIST:"):
                    users = message[len("USERLIST:"):].split(",")
                    self.online_users = [u for u in users if u != self.nickname and u.strip()]
                    self.filter_user_list()
                elif message.startswith("!SYSTEM!"):
                    sys_msg = message[len("!SYSTEM!"):]
                    self.display_message(sys_msg, 'system')
                    self.request_user_list()
                elif message.startswith("!PRIVATE!"):
                    parts = message[len("!PRIVATE!:"):].split(":", 1)
                    if len(parts) == 2:
                        sender, msg = parts
                        self.handle_private_message(sender, msg)
                else:
                    timestamp = datetime.now().strftime("%H:%M")
                    self.display_message(f"[{timestamp}] {message}", 'other')
            except Exception as e:
                print(f"[Ошибка] {e}")
                self.connected = False
                self.update_send_button_state()
                break

    def handle_private_message(self, sender, message):
        """Обработка личных сообщений"""
        timestamp = datetime.now().strftime("%H:%M")
        formatted_msg = f"[{timestamp}] {sender}: {message}"

        if sender in self.private_chats:
            try:
                # Показываем сообщение в окне личного чата
                self.private_chats[sender].display_message(formatted_msg, 'other')
                self.private_chats[sender].save_private_message(timestamp, sender, message, 'other')
            except tk.TclError:
                pass
        else:
            # Если нет открытого окна — создаём новое
            self.start_private_chat(None, sender)
            try:
                self.private_chats[sender].display_message(formatted_msg, 'other')
                self.private_chats[sender].save_private_message(timestamp, sender, message, 'other')
            except tk.TclError:
                pass
            self.display_message(f"Система: Новое личное сообщение от {sender}", 'system')

    def request_user_list(self):
        if self.connected:
            try:
                self.sock.send(self.fernet.encrypt("/getusers".encode()))
            except:
                pass

    def start_private_chat(self, event, recipient=None):
        if not recipient:
            selection = self.user_listbox.curselection()
            if not selection:
                return
            recipient = self.user_listbox.get(selection[0])
        if recipient == "Ничего не найдено":
            return
        if recipient not in self.private_chats:
            self.private_chats[recipient] = PrivateChatWindow(
                self.root,
                self.nickname,
                recipient,
                self.fernet,
                self.sock,
                self,
                self.password
            )
            self.display_message(f"Система: Вы начали личный чат с {recipient}", 'system')

    def on_close(self):
        if self.connected:
            try:
                self.sock.send(self.fernet.encrypt("/quit".encode()))
                self.sock.close()
            except:
                pass
        for chat in list(self.private_chats.values()):
            chat.on_close()
        self.root.destroy()

    def update_user_list_timer(self):
        if self.connected:
            self.request_user_list()
        self.root.after(30000, self.update_user_list_timer)


if __name__ == "__main__":
    root = tk.Tk()
    app = SecureChatClient(root)
    root.mainloop()