from PyQt5.QtWidgets import *


class ExtratextView(QWidget):
    def __init__(self, name=''):
        super().__init__()
        self.textview = QTextEdit()
        self.label = QLabel(name)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.text = self.document().toPlainText
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.textview)
        self.weight = 1

    def document(self):
        return self.textview.document()

    def setPlainText(self, text):
        self.textview.setPlainText(text)

    def toPlainText(self):
        return self.textview.toPlainText()




