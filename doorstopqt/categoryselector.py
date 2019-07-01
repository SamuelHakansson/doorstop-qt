from PyQt5.QtWidgets import *


class CategorySelector(QWidget):
    def __init__(self, parent=None):
        super(CategorySelector, self).__init__(parent)
        self.grid = QHBoxLayout()
        self.grid.setSpacing(10)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.grid.addWidget(self.combo)
        self.setLayout(self.grid)
        self.db = None
        self.lastcategory = None
        def updatelastcategory(index):
            self.lastcategory = self.text(index)
        self.combo.currentIndexChanged.connect(updatelastcategory)

    def connectdb(self, db):
        self.db = db
        self.buildlist()

    def buildlist(self):
        self.combo.blockSignals(True)
        lastcategory = self.lastcategory
        if self.db is None or len(self.db.root.documents) == 0:
            return
        self.combo.clear()
        graph = self.db.root.draw().split('\n')
        self.combo.addItems([x for x in graph if x.split()[-1].isidentifier()])
        self.select(lastcategory)
        self.combo.blockSignals(False)

    def clear(self):
        self.combo.clear()

    def callback(self, func):
        def clb(index):
            func(self.text(index))
        self.combo.currentIndexChanged.connect(clb)

    def text(self, index=None):
        if self.combo.count() == 0:
            return None
        elif index is not None:
            return self.combo.itemText(index).split()[-1]
        else:
            return self.combo.itemText(self.combo.currentIndex()).split()[-1]

    def select(self, category=None):
        if category is None:
            self.combo.setCurrentIndex(0)
        else:
            for i in range(len(self.combo)):
                if self.text(i) == category:
                    self.combo.setCurrentIndex(i)
                    return

