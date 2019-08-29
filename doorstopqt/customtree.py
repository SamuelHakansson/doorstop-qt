from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class CustomTree(QTreeView):
    def __init__(self):
        super(CustomTree, self).__init__()
        self.setIndentation(20)
        self.setDragDropMode(self.InternalMove)
        self.setSelectionBehavior(self.SelectRows)

    def dropEvent(self, a0: QDropEvent) -> None:
        position = a0.pos()
        index = self.indexAt(position)
        if index.column() == 0:
            super().dropEvent(a0)
