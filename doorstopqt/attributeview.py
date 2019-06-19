from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from doorstop.common import DoorstopError


class AttributeView(QWidget):
    def __init__(self, parent=None):
        super(AttributeView, self).__init__(parent)

        self.db = None
        self.currentuid = None

        grid = QHBoxLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        self.active = QCheckBox('Active')
        self.derived = QCheckBox('Derived')
        self.normative = QCheckBox('Normative')
        self.heading = QCheckBox('Heading')
        self.reflabel = QLabel('External ref:')
        self.refloc = QLabel('')
        self.ref = QLineEdit()
        self.reflabel.setVisible(False)
        self.ref.setVisible(False)
        self.refloc.setVisible(False)
        self.markreviewed = QPushButton('Mark as reviewed')
        self.markreviewed.setVisible(False)

        def active(s):
            if self.currentuid is None:
                return
            data = self.db.find(self.currentuid)
            data.active = True if s == Qt.Checked else False
            self.read(self.currentuid)
            #self.db.reload()
        self.active.stateChanged.connect(active)
        
        def derived(s):
            if self.currentuid is None:
                return
            data = self.db.find(self.currentuid)
            data.derived = True if s == Qt.Checked else False
            self.read(self.currentuid)
            #self.db.reload()
        self.derived.stateChanged.connect(derived)

        def normative(s):
            if self.currentuid is None:
                return
            data = self.db.find(self.currentuid)
            data.normative = True if s == Qt.Checked else False
            self.read(self.currentuid)
            #self.db.reload()
        self.normative.stateChanged.connect(normative)

        def heading(s):
            if self.currentuid is None:
                return
            data = self.db.find(self.currentuid)
            data.heading = True if s == Qt.Checked else False
            self.read(self.currentuid)
            #self.db.reload()
        self.heading.stateChanged.connect(heading)

        def ref():
            if self.currentuid is None:
                return
            data = self.db.find(self.currentuid)
            data.ref = self.ref.text()
            self.read(self.currentuid)
            self.setFocus(False)
        self.ref.editingFinished.connect(ref)
        self.ref.returnPressed.connect(ref)

        def markreviewed():
            if self.currentuid is None:
                return
            data = self.db.find(self.currentuid)
            data.review()
            data.clear()
            self.read(self.currentuid)
            #self.db.reload()
        self.markreviewed.clicked.connect(markreviewed)

        grid.addWidget(self.active)
        grid.addWidget(self.derived)
        grid.addWidget(self.normative)
        grid.addWidget(self.heading)
        grid.addWidget(self.reflabel)
        grid.addWidget(self.ref)
        grid.addWidget(self.refloc)
        grid.addStretch(1)
        grid.addWidget(self.markreviewed)
        self.setLayout(grid)

    def connectdb(self, db):
        self.db = db
        self.read(self.currentuid)

    def read(self, uid):
        if uid is None:
            return
        self.currentuid = None
        if self.db is None:
            return
        data = self.db.find(uid)
        if data is None:
            return

        self.active.setCheckState(Qt.Checked if data.active else Qt.Unchecked)
        self.derived.setCheckState(Qt.Checked if data.derived else Qt.Unchecked)
        self.normative.setCheckState(Qt.Checked if data.normative else Qt.Unchecked)
        self.heading.setCheckState(Qt.Checked if data.heading else Qt.Unchecked)
        self.ref.setText(data.ref)
        self.refloc.setText('')
        if data.ref != '':
            try:
                refloc = data.find_ref()
            except DoorstopError:
                self.refloc.setText('(not found)')
            else:
                if refloc[1]:
                    self.refloc.setText('{}:{}'.format(refloc[0], refloc[1]))
                else:
                    self.refloc.setText('{}'.format(refloc[0]))
        if data.reviewed and data.cleared:
            self.markreviewed.setVisible(False)
        else:
            self.markreviewed.setVisible(True)
        self.currentuid = uid

    def read_current(self, uid):
        if uid == self.currentuid:
            self.read(uid)


    def showref(self, b):
        if b:
            self.reflabel.setVisible(True)
            self.ref.setVisible(True)
            self.refloc.setVisible(True)
            self.active.setVisible(False)
            self.derived.setVisible(False)
            self.normative.setVisible(False)
            self.heading.setVisible(False)
        else:
            self.reflabel.setVisible(False)
            self.ref.setVisible(False)
            self.refloc.setVisible(False)
            self.active.setVisible(True)
            self.derived.setVisible(True)
            self.normative.setVisible(True)
            self.heading.setVisible(True)
