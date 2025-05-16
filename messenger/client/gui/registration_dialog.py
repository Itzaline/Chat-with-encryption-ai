from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel
from PyQt6.QtGui import QPixmap

class RegistrationDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registration")
        layout = QVBoxLayout()
        
        self.username_input = QLineEdit(placeholderText="Username")
        self.display_name_input = QLineEdit(placeholderText="Display Name")
        self.avatar_label = QLabel()
        self.avatar_btn = QPushButton("Select Avatar")
        self.submit_btn = QPushButton("Register")
        
        self.avatar_btn.clicked.connect(self.select_avatar)
        layout.addWidget(self.username_input)
        layout.addWidget(self.display_name_input)
        layout.addWidget(self.avatar_label)
        layout.addWidget(self.avatar_btn)
        layout.addWidget(self.submit_btn)
        
        self.setLayout(layout)
        self.avatar_path = ""

    def select_avatar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Avatar", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.avatar_path = path
            pixmap = QPixmap(path).scaled(100, 100)
            self.avatar_label.setPixmap(pixmap)