import sys
from qasync import QApplication, asyncSlot
from gui.auth_window import AuthWindow
from network.client import NetworkClient
from crypto.crypto_manager import CryptoManager

class App:
    def __init__(self):
        self.current_user = None
        self.crypto = CryptoManager()  # Создаем экземпляр крипто-менеджера
        self.network = NetworkClient(self.crypto)  # Передаем его в сетевой клиент
        self.auth_window = AuthWindow()
        self.connect_signals()
        self.auth_window.show()
    
    def connect_signals(self):
        # Подключаем обработчики форм
        self.auth_window.login_form.login_btn.clicked.connect(self.handle_login)
        self.auth_window.registration_form.register_btn.clicked.connect(self.handle_register)
    
    async def handle_login(self):
        form = self.auth_window.login_form
        username = form.username_input.text()
        password = form.password_input.text()
        
        try:
            response = await self.network.login(username, password)
            self.current_user = response['user']
            self.show_main_window()
        except Exception as e:
            form.error_label.setText(str(e))
    
    async def handle_register(self):
        form = self.auth_window.registration_form
        user_data = {
            "username": form.username_input.text(),
            "display_name": form.display_name_input.text(),
            "password": form.password_input.text(),
            "avatar": getattr(form, 'avatar_path', "")
        }
        
        try:
            response = await self.network.register(user_data)
            self.current_user = response['user']
            self.show_main_window()
        except Exception as e:
            form.error_label.setText(str(e))
    
    def show_main_window(self):
        from gui.main_window import MainWindow
        self.main_window = MainWindow(self.current_user)
        self.auth_window.close()
        self.main_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = App()
    sys.exit(app.exec())