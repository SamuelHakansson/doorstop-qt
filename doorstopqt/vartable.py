import json

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class VarTable(QWidget):
    def __init__(self, name=None, label=None):
        super().__init__()
        rows = 1
        columns = 3
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.table = QTableWidget(rows, columns)
        self.table.setAlternatingRowColors(True)
        self.weight = 1
        self.name = name
        self.label = label
        self.text = self.tableastext
        self.layout.addWidget(QLabel(self.label))
        self.layout.addWidget(self.table)
        self.headers = ["Name", "Value", "Unit"]
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.cellChanged.connect(self.newrow)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def newrow(self):
        columns = self.table.columnCount()
        for i in range(columns):
            it = self.table.item(0, i)
            if not it or not it.text():
                return
        self.table.insertRow(0)

    def tableastext(self):
        tables = []
        for i in range(self.table.rowCount()):
            entry = {}
            for j, header in enumerate(self.headers):
                if self.table.item(i, j):
                    entry[header] = self.table.item(i, j).text()
            if entry:
                tables.append(entry)
        print(tables, flush=True)
        return ''.join(json.dumps(entry) for entry in tables)

    def setPlainText(self, text):
        pass

    def toPlainText(self):
        return ""

