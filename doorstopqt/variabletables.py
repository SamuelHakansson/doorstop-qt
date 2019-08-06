from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .vartable import VarTable


class VariableTables(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.inputtable = VarTable("inputvariables", "Input variables")
        self.outputtable = VarTable("expectedresults", "Expected results")
        self.weight = 3
        self.name = "variables"
        self.layout.addWidget(self.inputtable)
        self.layout.addWidget(self.outputtable)
        self.views = [self.inputtable, self.outputtable]



