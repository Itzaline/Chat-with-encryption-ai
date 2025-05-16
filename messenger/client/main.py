import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from network.client import NetworkClient
from crypto.crypto_manager import CryptoManager
from gui.registration_dialog import RegistrationDialog

class App:
    def __init__(self):
        self.current_user = None
        self.crypto = CryptoManager("secret_password")
        self.network = NetworkClient(self.crypto)
        self.setup_ui()
        
    def setup_ui(self):
        self.app = QApplication(sys.argv)
        self.show_registration_dialog()
        self.app.exec()

    def show_registration_dialog(self):
        self.registration_dialog = RegistrationDialog()
        self.registration_dialog.submit_btn.clicked.connect(self.on_registration)
        self.registration_dialog.show()

    def on_registration(self):
        username = self.registration_dialog.username_input.text()
        display_name = self.registration_dialog.display_name_input.text()
        avatar = self.registration_dialog.avatar_path
        
        self.current_user = {
            "username": username,
            "display_name": display_name,
            "avatar": avatar
        }
        
        self.main_window = MainWindow()
        self.main_window.show()
        self.registration_dialog.close()

if __name__ == "__main__":
    App()