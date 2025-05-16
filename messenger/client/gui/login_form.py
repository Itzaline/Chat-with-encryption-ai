from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel

class LoginForm(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.username_input = QLineEdit(placeholderText="Username")
        self.password_input = QLineEdit(placeholderText="Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_btn = QPushButton("Login")
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.error_label)
        
        self.setLayout(layout)