from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .vartable import VarTable
from .markdownview import MarkdownViewExt


class VariableTables(QSplitter):
    def __init__(self):
        super().__init__()
        self.inputtable = VarTable("inputvariables", "Input variables")
        self.expectedresultsmarkdownview = MarkdownViewExt(text='Expected results')
        self.expectedresultsmarkdownview.name = 'expectedresults'

        self.weight = 3
        self.name = "variables"
        self.addWidget(self.inputtable)
        self.addWidget(self.expectedresultsmarkdownview)
        self.views = [self.inputtable, self.expectedresultsmarkdownview]




