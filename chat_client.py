import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk, font, Listbox, Entry, Toplevel
from cryptography.fernet import Fernet
from datetime import datetime
import json
import os

SERVER_IP = 'localhost'
PORT = 25564

class PrivateChatWindow:
    def __init__(self, root, nickname, recipient, fernet, sock, client):
        self.root = root
        self.nickname = nickname
        self.recipient = recipient
        self.fernet = fernet
        self.sock = sock
        self.client = client  # Ссылка на SecureChatClient для обратной связи

        self.window = Toplevel(root)
        self.window.title(f"Личный чат с {recipient}")
        self.window.geometry("600x500")
        self.is_closed = False  # Флаг для отслеживания состояния окна

        # Область чата
        self.text_area = scrolledtext.ScrolledText(
            self.window,
            state='disabled',
            wrap=tk.WORD,
            font=('Helvetica', 11),
            padx=10,
            pady=10,
            bg='white'
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # Настройка тегов
        self.text_area.tag_config('self', foreground='#2d572c')
        self.text_area.tag_config('other', foreground='#8a2be2')

        # Панель ввода
        input_frame = ttk.Frame(self.window)
        input_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        self.entry = ttk.Entry(input_frame, font=('Helvetica', 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", lambda e: self.send_message())

        send_btn = ttk.Button(input_frame, text="Отправить", command=self.send_message)
        send_btn.pack(side=tk.RIGHT)

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Загрузка истории сообщений
        self.load_private_messages()

        # Фокус на поле ввода
        self.entry.focus_set()

    def get_chat_filename(self):
        """Возвращает имя JSON-файла для чата, сортируя никнеймы по алфавиту"""
        users = sorted([self.nickname, self.recipient])
        return f"{users[0]}_{users[1]}.json"

    def save_private_message(self, timestamp, sender, message, tag):
        """Сохранение сообщения в JSON-файл"""
        if self.is_closed:
            return
        message_data = {
            "timestamp": timestamp,
            "sender": sender,
            "message": message,
            "tag": tag
        }
        filename = self.get_chat_filename()
        try:
            # Читаем существующие сообщения
            messages = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            messages.append(message_data)
            # Сохраняем обновлённый список
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Ошибка] Не удалось сохранить сообщение: {e}")

    def load_private_messages(self):
        """Загрузка истории сообщений из JSON-файла"""
        filename = self.get_chat_filename()
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                for msg in messages:
                    formatted_msg = f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}"
                    self.display_message(formatted_msg, msg['tag'])
        except Exception as e:
            print(f"[Ошибка] Не удалось загрузить историю сообщений: {e}")

    def send_message(self):
        """Отправка личного сообщения"""
        if self.is_closed:
            return
        message = self.entry.get().strip()
        if message:
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
        """Отображение сообщения"""
        if not self.is_closed and self.window.winfo_exists():
            try:
                self.text_area.configure(state='normal')
                self.text_area.insert(tk.END, msg + "\n", tag)
                self.text_area.configure(state='disabled')
                self.text_area.yview(tk.END)
            except tk.TclError:
                pass  # Игнорируем ошибки, если виджет уже уничтожен

    def on_close(self):
        """Закрытие окна"""
        self.is_closed = True
        try:
            self.window.destroy()
            # Уведомляем основной клиент о закрытии окна
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
        self.nickname = self.get_nickname()
        if not self.nickname:
            root.destroy()
            return

        self.connected = False
        self.private_chats = {}  # {recipient: PrivateChatWindow}
        self.online_users = []
        self.setup_ui()
        self.connect_to_server()

    def setup_styles(self):
        """Настройка стилей"""
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', padding=6, relief='flat', background='#4a7a8c')
        self.style.configure('TEntry', padding=6)
        self.style.map('TButton',
                       background=[('active', '#5a8a9c'), ('disabled', '#cccccc')])

        self.text_font = font.Font(family='Helvetica', size=11)
        self.alert_font = font.Font(family='Helvetica', size=11, weight='bold')
        self.status_font = font.Font(family='Helvetica', size=9)
        self.userlist_font = font.Font(family='Helvetica', size=10)

    def get_nickname(self):
        """Получение никнейма"""
        nickname = simpledialog.askstring(
            "Никнейм",
            "Введите ваш никнейм:",
            parent=self.root
        )
        return nickname

    def setup_ui(self):
        """Настройка интерфейса"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Фрейм списка пользователей
        user_frame = ttk.Frame(main_frame, width=200)
        user_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Поиск пользователей
        search_frame = ttk.Frame(user_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_user_list)

        self.search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=self.userlist_font
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        clear_btn = ttk.Button(search_frame, text="X", width=3, command=self.clear_search)
        clear_btn.pack(side=tk.RIGHT)

        self.user_list_label = ttk.Label(
            user_frame,
            text="Пользователи онлайн:",
            font=self.userlist_font
        )
        self.user_list_label.pack(pady=(0, 5))

        self.user_listbox = Listbox(
            user_frame,
            font=self.userlist_font,
            selectbackground='#4a7a8c',
            selectforeground='white'
        )
        self.user_listbox.pack(fill=tk.BOTH, expand=True)
        self.user_listbox.bind("<Double-Button-1>", self.start_private_chat)

        # Кнопка обновления
        refresh_btn = ttk.Button(
            user_frame,
            text="Обновить список",
            command=self.request_user_list
        )
        refresh_btn.pack(fill=tk.X, pady=(5, 0))

        # Основной чат
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.chat_title = ttk.Label(
            chat_frame,
            text="Общий чат",
            font=self.alert_font
        )
        self.chat_title.pack(pady=(0, 5))

        self.text_area = scrolledtext.ScrolledText(
            chat_frame,
            state='disabled',
            wrap=tk.WORD,
            font=self.text_font,
            padx=10,
            pady=10,
            bg='white'
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # Теги для сообщений
        self.text_area.tag_config('alert', foreground='red', font=self.alert_font)
        self.text_area.tag_config('system', foreground='blue', font=self.text_font)
        self.text_area.tag_config('self', foreground='#2d572c', font=self.text_font)
        self.text_area.tag_config('other', foreground='black', font=self.text_font)

        # Панель ввода
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.entry = ttk.Entry(input_frame, font=self.text_font)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry.bind("<Return>", lambda e: self.send_message())
        self.entry.bind("<KeyRelease>", self.update_send_button_state)

        self.send_btn = ttk.Button(
            input_frame,
            text="Отправить",
            command=self.send_message,
            state='disabled'
        )
        self.send_btn.pack(side=tk.RIGHT)

        # Статус
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_label = ttk.Label(
            self.status_frame,
            text="Подключение...",
            font=self.status_font,
            foreground='#666666'
        )
        self.status_label.pack(side=tk.LEFT)

        # Таймер обновления
        self.update_user_list_timer()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def filter_user_list(self, *args):
        """Фильтрация списка пользователей"""
        search_term = self.search_var.get().lower()
        self.user_listbox.delete(0, tk.END)

        for user in self.online_users:
            if search_term in user.lower():
                self.user_listbox.insert(tk.END, user)

        if not search_term and not self.user_listbox.size():
            for user in self.online_users:
                self.user_listbox.insert(tk.END, user)
        elif not self.user_listbox.size():
            self.user_listbox.insert(tk.END, "Ничего не найдено")

    def clear_search(self):
        """Очистка поиска"""
        self.search_var.set("")
        self.search_entry.focus()

    def update_user_list_timer(self):
        """Автоматическое обновление списка"""
        if self.connected:
            self.request_user_list()
        self.root.after(30000, self.update_user_list_timer)

    def update_send_button_state(self, event=None):
        """Активация кнопки отправки"""
        if self.entry.get().strip() and self.connected:
            self.send_btn.configure(state='normal')
        else:
            self.send_btn.configure(state='disabled')

    def connect_to_server(self):
        """Подключение к серверу"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_IP, PORT))

            key = self.sock.recv(44)
            self.fernet = Fernet(key)
            self.sock.send(self.fernet.encrypt(self.nickname.encode()))

            self.connected = True
            self.update_status("Подключено", "#2d572c")
            self.update_send_button_state()

            self.request_user_list()
            threading.Thread(target=self.receive_messages, daemon=True).start()

        except Exception as e:
            self.update_status(f"Ошибка подключения: {e}", "red")
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
            self.root.after(1000, self.root.destroy())

    def update_status(self, text, color="#666666"):
        """Обновление статуса"""
        self.status_label.config(text=text, foreground=color)

    def send_message(self):
        """Отправка сообщения в общий чат"""
        message = self.entry.get().strip()
        if message and self.connected:
            try:
                encrypted = self.fernet.encrypt(message.encode())
                self.sock.send(encrypted)

                timestamp = datetime.now().strftime("%H:%M")
                self.display_message(
                    f"[{timestamp}] Вы: {message}",
                    'self'
                )
                self.entry.delete(0, tk.END)
                self.update_send_button_state()
            except Exception as e:
                self.update_status(f"Ошибка отправки: {e}", "red")
                messagebox.showerror("Ошибка", f"Ошибка отправки: {e}")
                self.connected = False
                self.update_send_button_state()

    def display_message(self, msg, tag='other'):
        """Отображение сообщения в основном чате"""
        try:
            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, msg + "\n", tag)
            self.text_area.configure(state='disabled')
            self.text_area.yview(tk.END)
        except tk.TclError:
            pass  # Игнорируем ошибки, если виджет уничтожен

    def receive_messages(self):
        """Получение сообщений от сервера"""
        while True:
            try:
                encrypted = self.sock.recv(4096)
                if not encrypted:
                    print("[Отладка] Соединение с сервером разорвано: пустые данные")
                    break

                message = self.fernet.decrypt(encrypted).decode()

                if message.startswith("USERLIST:"):
                    users = message[len("USERLIST:"):].split(",")
                    self.online_users = [u for u in users if u != self.nickname and u.strip() != ""]
                    self.filter_user_list()

                elif message.startswith("!SYSTEM!"):
                    sys_msg = message[len("!SYSTEM!"):]
                    self.display_message(sys_msg, 'system')

                    if "присоединился" in sys_msg or "покинул" in sys_msg:
                        self.request_user_list()

                elif message.startswith("!PRIVATE!"):
                    parts = message[len("!PRIVATE!"):].split(":", 1)
                    if len(parts) == 2:
                        sender, msg = parts
                        self.handle_private_message(sender, msg)

                else:
                    timestamp = datetime.now().strftime("%H:%M")
                    self.display_message(f"[{timestamp}] {message}", 'other')

            except Exception as e:
                print(f"[Ошибка в receive_messages] {e}")
                self.update_status(f"Соединение прервано: {e}", "red")
                self.connected = False
                self.update_send_button_state()
                break

    def handle_private_message(self, sender, message):
        """Обработка личного сообщения"""
        timestamp = datetime.now().strftime("%H:%M")
        formatted_msg = f"[{timestamp}] {sender}: {message}"

        if sender in self.private_chats:
            # Если окно чата уже открыто
            try:
                self.private_chats[sender].display_message(formatted_msg, 'other')
                self.private_chats[sender].save_private_message(timestamp, sender, message, 'other')
            except tk.TclError:
                pass  # Игнорируем, если окно было закрыто
        else:
            # Создаем новое окно чата
            self.start_private_chat(None, sender)
            try:
                self.private_chats[sender].display_message(formatted_msg, 'other')
                self.private_chats[sender].save_private_message(timestamp, sender, message, 'other')
            except tk.TclError:
                pass

            # Уведомление в основном чате
            self.display_message(
                f"Система: Новое личное сообщение от {sender}",
                'system'
            )

    def request_user_list(self):
        """Запрос списка пользователей"""
        if self.connected:
            try:
                self.sock.send(self.fernet.encrypt("/getusers".encode()))
            except Exception as e:
                print(f"Ошибка запроса списка пользователей: {e}")

    def start_private_chat(self, event, recipient=None):
        """Открытие окна личного чата"""
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
                self
            )

            # Уведомление в основном чате
            self.display_message(
                f"Система: Вы начали личный чат с {recipient}",
                'system'
            )

    def on_close(self):
        """Закрытие клиента"""
        if self.connected:
            try:
                self.sock.send(self.fernet.encrypt("/quit".encode()))
                self.sock.close()
            except:
                pass

        # Закрываем все окна личных чатов
        for chat in list(self.private_chats.values()):
            chat.on_close()

        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SecureChatClient(root)
    root.mainloop()
