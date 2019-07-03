from PyQt5.QtWidgets import *
from .categoryselector import CategorySelector
import re

class CreateCategoryDialog(QDialog):
    def __init__(self, parent=None):
        super(CreateCategoryDialog, self).__init__(parent)

        self.setWindowTitle('Create new category')
        self.vbox = QVBoxLayout()
        grid = QGridLayout()
        self.prefix = QLineEdit()
        self.catsel = CategorySelector()
        self.path = QLineEdit('./reqs/')
        self.create = QPushButton('Create')
        self.create.setEnabled(False)
        grid.addWidget(QLabel('Prefix:'), 0, 0)
        grid.addWidget(self.prefix, 0, 1)
        grid.addWidget(QLabel('Parent:'), 1, 0)
        grid.addWidget(self.catsel, 1, 1)
        grid.addWidget(QLabel('Path:'), 2, 0)
        grid.addWidget(self.path, 2, 1)
        self.db = None
        self.badcharacters = ['<', '>', ':', '/', '\\', '|', '?', '*']

        def updatepath(s):
            path = self.path.text()
            lastslash = path.rfind('/')
            if lastslash == -1:
                path = './reqs/' + s.lower()
            else:
                path = path[:lastslash + 1] + s.lower()
            self.path.setText(path)
            if self.prefix.text():
                for char in self.badcharacters:
                    if char in self.prefix.text():
                        self.create.setEnabled(False)
                        self.warning.setText(self.warningtext)
                        return
                self.create.setEnabled(True)
                self.warning.setText('')
            else:
                self.create.setEnabled(False)
                self.warning.setText('')
        self.prefix.textChanged.connect(updatepath)

        def create(b):
            self.hide()
            prefix = self.prefix.text()
            path = self.path.text()
            parent = self.catsel.text()
            print('{} {} {}'.format(prefix, parent, path))
            self.prefix.setText('')
            self.db.root.create_document(path, prefix, parent=parent)
            self.db.reload()
        self.create.clicked.connect(create)

        g = QWidget()
        g.setLayout(grid)
        self.vbox.addWidget(g)
        self.warningtext = 'Invalid character(s)'
        self.warning = QLabel()
        self.warning.setStyleSheet('color: red')
        self.vbox.addWidget(self.warning)
        self.vbox.addWidget(self.create)
        self.setLayout(self.vbox)

    def show(self):
        super(CreateCategoryDialog, self).show()
        self.prefix.setFocus()
        self.raise_()

    def connectdb(self, db):
        self.db = db
        self.catsel.connectdb(db)
