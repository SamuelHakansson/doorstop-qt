from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class DecisiontakersView(QWidget):
    def __init__(self, name):
        super().__init__()
        self.text = self.createdecisiontakerslist
        self.listview = QListView()
        #self.listview.setAlternatingRowColors(True)
        self.label = QLabel(name)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.listview)
        self.weight = 1
        self.model = QStandardItemModel()
        self.listview.setModel(self.model)
        #self.listview.setDragDropMode()
        self.listview.model().dataChanged.connect(self.checkrows)
        self.rows = self.listview.model().rowCount

    def checkrows(self):
        item = self.listview.model().index(self.rows()-1, 0)
        name = item.data()
        if name:
            self.additem()

    def additem(self, text=None):
        item = QStandardItem(text)
        item.setEditable(True)
        item.setSelectable(True)
        self.model.appendRow(item)

    def setPlainText(self, decisiontakers):
        self.model.clear()
        if decisiontakers:
            for decisiontaker in decisiontakers:
                self.additem(decisiontaker)
            self.additem()
        while self.model.rowCount() < 4:
            self.additem()

    def createdecisiontakerslist(self):
        decisiontakerslist = []
        for row in range(self.rows()):
            item = self.listview.model().index(row, 0)
            name = item.data()
            if name:
                decisiontakerslist.append(name)
        return decisiontakerslist