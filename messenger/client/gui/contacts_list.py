from PyQt6.QtWidgets import QListWidget, QMenu
from PyQt6.QtCore import Qt, pyqtSignal

class ContactsList(QListWidget):
    contact_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(True)
        self.itemDoubleClicked.connect(self.on_contact_selected)
        
    def on_contact_selected(self, item):
        self.contact_selected.emit(item.text())