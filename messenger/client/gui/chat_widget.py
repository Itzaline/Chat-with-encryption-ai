from PyQt6.QtWidgets import QWidget, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap  # Добавлен импорт QPixmap
from PyQt6.QtCore import pyqtSignal

class ChatMessageWidget(QWidget):
    def __init__(self, sender: str, avatar: str, message: str):
        super().__init__()
        layout = QHBoxLayout()
        
        self.avatar_label = QLabel()
        pixmap = QPixmap(avatar).scaled(50, 50)
        self.avatar_label.setPixmap(pixmap)
        
        self.content = QTextEdit()
        self.content.setHtml(f"<b>{sender}:</b><br>{message}")
        self.content.setReadOnly(True)
        
        layout.addWidget(self.avatar_label)
        layout.addWidget(self.content)
        self.setLayout(layout)

class ChatWidget(QWidget):
    message_sent = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.chat_history = QVBoxLayout()
        self.message_input = QLineEdit()
        self.send_button = QPushButton("Send")
        
        layout.addLayout(self.chat_history)
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)
        self.send_button.clicked.connect(self.on_send)
        
    def add_message(self, sender: str, avatar: str, message: str):
        widget = ChatMessageWidget(sender, avatar, message)
        self.chat_history.addWidget(widget)
        
    def on_send(self):
        text = self.message_input.text()
        if text:
            self.message_sent.emit(text)
            self.message_input.clear()