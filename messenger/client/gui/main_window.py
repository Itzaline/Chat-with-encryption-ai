from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from .chat_widget import ChatWidget
from .contacts_list import ContactsList

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SecureChat")
        self.setGeometry(100, 100, 800, 600)
        
        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        
        self.contacts = ContactsList()
        self.chat = ChatWidget()
        
        layout.addWidget(self.contacts, 1)
        layout.addWidget(self.chat, 3)
        self.setCentralWidget(main_widget)