from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
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