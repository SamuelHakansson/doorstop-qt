import json

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class VarTable(QWidget):
    def __init__(self, name=None, label=None):
        super().__init__()
        self.rows = 1
        self.columns = 3
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.table = QTableWidget(self.rows, self.columns)
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
        rows = self.table.rowCount()
        for i in range(columns):
            it = self.table.item(rows-1, i)
            if not it or not it.text():
                return
        self.table.insertRow(rows)

    def tableastext(self):
        tables = []
        for i in range(self.table.rowCount()):
            entry = {}
            for j, header in enumerate(self.headers):
                if self.table.item(i, j):
                    entry[header] = self.table.item(i, j).text()
            if entry:
                tables.append(entry)
        text = json.dumps(tables)
        return text

    def setPlainText(self, text):
        if text is not None and text != "":
            data = json.loads(text)
            j = 0
            for i, vars in enumerate(data):
                for key, value in vars.items():
                    self.table.setItem(0, j, QTableWidgetItem(value))
                    j += 1
        else:
            self.table.clearContents()
            self.table.setRowCount(self.rows)

    def toPlainText(self):
        return self.tableastext()

