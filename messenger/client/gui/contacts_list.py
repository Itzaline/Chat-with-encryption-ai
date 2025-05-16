from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QHBoxLayout, QLabel  # Добавлены импорты
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

class ContactsList(QListWidget):
    contact_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(True)
        self.itemDoubleClicked.connect(self.on_contact_selected)
        
    def on_contact_selected(self, item):
        self.contact_selected.emit(item.text())
        
    def add_contact(self, username: str, display_name: str, avatar: str):
        item = QListWidgetItem()
        widget = QWidget()
        layout = QHBoxLayout()
        
        avatar_label = QLabel()
        pixmap = QPixmap(avatar).scaled(30, 30)
        avatar_label.setPixmap(pixmap)
        
        name_label = QLabel(display_name)
        
        layout.addWidget(avatar_label)
        layout.addWidget(name_label)
        widget.setLayout(layout)
        
        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)