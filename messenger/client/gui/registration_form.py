from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog
from PyQt6.QtGui import QPixmap

class RegistrationForm(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.username_input = QLineEdit(placeholderText="Username")
        self.display_name_input = QLineEdit(placeholderText="Display Name")
        self.password_input = QLineEdit(placeholderText="Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.avatar_label = QLabel()
        self.avatar_btn = QPushButton("Select Avatar")
        self.register_btn = QPushButton("Register")
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        
        self.avatar_btn.clicked.connect(self.select_avatar)
        
        layout.addWidget(self.username_input)
        layout.addWidget(self.display_name_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.avatar_label)
        layout.addWidget(self.avatar_btn)
        layout.addWidget(self.register_btn)
        layout.addWidget(self.error_label)
        
        self.setLayout(layout)
    
    def select_avatar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Avatar", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.avatar_path = path
            pixmap = QPixmap(path).scaled(100, 100)
            self.avatar_label.setPixmap(pixmap)