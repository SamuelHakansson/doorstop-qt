from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class ExtratextView(QTextEdit):
    def __init__(self, name=''):
        super().__init__()
        self.label = QLabel(name)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.text = self.document().toPlainText





