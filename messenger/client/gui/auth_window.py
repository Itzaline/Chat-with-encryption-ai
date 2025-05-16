from PyQt6.QtWidgets import QWidget, QStackedLayout, QVBoxLayout, QPushButton
from .login_form import LoginForm
from .registration_form import RegistrationForm
from qasync import asyncSlot

class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SecureChat - Authentication")
        self.setFixedSize(400, 300)
        
        # Создаем стековый layout
        self.stacked_layout = QStackedLayout()
        
        # Создаем формы
        self.login_form = LoginForm()
        self.registration_form = RegistrationForm()
        
        # Добавляем формы в стек
        self.stacked_layout.addWidget(self.login_form)
        self.stacked_layout.addWidget(self.registration_form)
        
        # Кнопки переключения
        switch_layout = QVBoxLayout()
        self.switch_to_login_btn = QPushButton("Already have an account? Login")
        self.switch_to_register_btn = QPushButton("Create new account")
        
        self.switch_to_login_btn.clicked.connect(self.show_login)
        self.switch_to_register_btn.clicked.connect(self.show_register)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.stacked_layout)
        main_layout.addLayout(switch_layout)
        main_layout.addWidget(self.switch_to_login_btn)
        main_layout.addWidget(self.switch_to_register_btn)
        
        self.setLayout(main_layout)
    
    def show_login(self):
        self.stacked_layout.setCurrentIndex(0)
        self.switch_to_login_btn.hide()
        self.switch_to_register_btn.show()
    
    def show_register(self):
        self.stacked_layout.setCurrentIndex(1)
        self.switch_to_register_btn.hide()
        self.switch_to_login_btn.show()