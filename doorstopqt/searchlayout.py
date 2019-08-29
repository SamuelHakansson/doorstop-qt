from .icon import Icon
from PyQt5.QtWidgets import *


class SearchLayout(QHBoxLayout):
    def __init__(self, placeholder='', iconcolor=None):
        super(SearchLayout, self).__init__()
        papirusicons = Icon(iconcolor)
        searchicon = papirusicons.fromTheme("search")
        clearicon = papirusicons.fromTheme("edit-clear-all")
        self.searchbox = QLineEdit()
        self.searchbox.setPlaceholderText(placeholder)
        self.searchlabel = QPushButton(searchicon, '')
        self.searchbox.setTextMargins(24, 0, 0, 0)
        self.searchlabel.setStyleSheet("background-color: 4e4e4e; border: 0px;")
        self.clearbutton = QPushButton(clearicon, '')
        self.clearbutton.setStyleSheet("background-color: 4e4e4e; border: 0px;")
        self.clearbutton.setParent(self.searchbox)
        self.addWidget(self.searchbox)
        self.searchlabel.setParent(self.searchbox)
        self.setSpacing(0)

        self.clearbutton.clicked.connect(self.clearsearchbox)
        self.icons = [searchicon, clearicon]

    def clearsearchbox(self):
        self.searchbox.setText('')

    def moveclearbutton(self):
        self.clearbutton.move(self.searchbox.width() - self.clearbutton.width(), self.clearbutton.pos().y())
