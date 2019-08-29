from PyQt5.QtWidgets import *
from .decisiontakersview import DecisiontakersView
from .extratextview import ExtratextView


class DecisionView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.decisionlog = ExtratextView('Decision log')
        self.decisiontakers = DecisiontakersView('Decision takers')
        self.decisionlog.weight = 10
        self.decisionlog.name = 'decisionlog'
        self.decisiontakers.name = 'decisiontakers'

        self.weight = 3
        self.name = "variables"
        self.layout.addWidget(self.decisionlog)
        self.layout.addWidget(self.decisiontakers)
        self.views = [self.decisionlog, self.decisiontakers]


