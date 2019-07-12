from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import datetime

class LastUpdatedText(QLabel):
    def __init__(self):
        super().__init__()
        self.name = None
        self.text = self.getcurrenttime
        self.weight = 1
        self.defaulttext = "Last updated: "

    def setPlainText(self, text):
        if text is None:
            text = ''
        self.setText(self.defaulttext + text)

    def toPlainText(self):
        return self.text()

    def getcurrenttime(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")