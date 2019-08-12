from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .markdownview import MarkdownView
from .icon import Icon
import sys


class ItemView(QVBoxLayout):
    def __init__(self, views=None, viewssplitted=None):
        super().__init__()
        self.db = None
        self.markdownview = MarkdownView()
        self.markdownview.name = 'text'
        self.views = [self.markdownview] + (views or [])
        for view in self.views:
            self.addWidget(view, view.weight)
        if viewssplitted:
            self.views = [self.markdownview] + (viewssplitted or [])
        self.currentuid = None

        papirusicons = Icon()
        reverticon = papirusicons.fromTheme("document-revert")
        saveicon = papirusicons.fromTheme("media-floppy")
        previewicon = papirusicons.fromTheme("document-preview")
        editicon = papirusicons.fromTheme("edit")

        self.previewbtn = QPushButton(previewicon, "Preview")
        self.previewbtn.clicked.connect(self.viewhtml)
        self.editbtn = QPushButton(editicon, "Edit")
        self.editbtn.clicked.connect(self.vieweditor)
        self.discardbtn = QPushButton(reverticon, "Revert")
        self.discardbtn.clicked.connect(self.discard)
        self.discardbtn.setVisible(False)
        self.savebtn = QPushButton(saveicon, "Save")
        self.savebtn.clicked.connect(self.save)
        self.savebtn.setVisible(False)
        discardbtnsize = self.discardbtn.minimumSizeHint()
        savebtnsize = self.savebtn.minimumSizeHint()
        if discardbtnsize.width() > savebtnsize.width():
            self.discardbtn.setFixedSize(discardbtnsize)
            self.savebtn.setFixedSize(discardbtnsize)
        else:
            self.discardbtn.setFixedSize(savebtnsize)
            self.savebtn.setFixedSize(savebtnsize)

        self.markdownview.editview.textChanged.connect(self.textChanged)
        self.markdownview.htmlview.selectionChanged.connect(self.vieweditor)

        saveshortcut = QShortcut(QKeySequence("Ctrl+S"), self.markdownview.editview)
        saveshortcut.activated.connect(lambda: self.save())
        saveshortcut = QShortcut(QKeySequence("Ctrl+S"), self.markdownview.htmlview)
        saveshortcut.activated.connect(lambda: self.save())

        buttongrid = QHBoxLayout()
        buttongrid.setContentsMargins(0, 0, 0, 0)
        buttongrid.addWidget(self.editbtn)
        buttongrid.addWidget(self.previewbtn)
        buttongrid.addWidget(self.discardbtn)
        buttongrid.addWidget(self.savebtn)
        buttonrow = QWidget()
        buttonrow.setLayout(buttongrid)
        self.addWidget(buttonrow)
        self.cache = {}
        self.CHANGED = 'changed'

    def connectdb(self, db):
        self.db = db
        self.read(self.currentuid)

    def textChanged(self):
        if self.currentuid is not None:
            self.cache[self.currentuid][self.CHANGED] = True
            self.savebtn.setVisible(True)
            self.discardbtn.setVisible(True)

    def viewhtml(self):
        self.markdownview.viewhtml()
        self.editbtn.setVisible(True)
        self.previewbtn.setVisible(False)
        #self.decisiontakers.setText(self.decisiontakerslabeltext)

    def vieweditor(self):
        self.markdownview.vieweditor()
        self.previewbtn.setVisible(True)
        self.editbtn.setVisible(False)
        #self.decisiontakers.setText(self.decisiontakerslabeltext)# + self.decisiontakerslabelhelp)

    def discard(self):
        if self.currentuid not in self.cache:
            return
        del self.cache[self.currentuid]
        uid = self.currentuid
        self.currentuid = None
        self.read(uid)

    def writetocache(self, view):
        self.cache[self.currentuid][view.name] = view.toPlainText()

    def readfromcache(self, view, uid):
        name = view.name
        if uid in self.cache and name in self.cache[uid]:
            text = self.cache[uid][name]
        else:
            text = self.getiteminfo(uid, name)
            print(text, flush=True)
        view.storedtext = text

    def read(self, uid):
        if uid is None:
            return
        if self.currentuid is not None:
            if self.currentuid in self.cache and self.cache[self.currentuid][self.CHANGED]:
                for view in self.views:
                    if view.name != 'lastupdated':
                        self.writetocache(view)

        for view in self.views:
            self.readfromcache(view, uid)

        self.savebtn.setVisible(False)
        self.discardbtn.setVisible(False)

        if uid in self.cache:
            if self.cache[uid][self.CHANGED]:
                self.savebtn.setVisible(True)
                self.discardbtn.setVisible(True)
        else:
            self.cache[uid] = {self.CHANGED: False}

        self.currentuid = None

        for view in self.views:
            view.setPlainText(view.storedtext)

        self.currentuid = uid
        self.viewhtml()

    def save(self):
        if self.currentuid is None:
            return
        if self.currentuid not in self.cache:
            return
        self.savefunc(self.currentuid)
        self.cache[self.currentuid][self.CHANGED] = False

        for view in self.views:
            name = view.name
            if name in self.cache[self.currentuid]:
                del self.cache[self.currentuid][name]
        #self.updateinfo(self.currentuid)
        self.savebtn.setVisible(False)
        self.discardbtn.setVisible(False)

    def savefunc(self, uid):
        for view in self.views:
            self.saveview(view, uid)

    def saveview(self, view, uid):
        text = view.text()
        item = self.db.find(uid)
        item.set(view.name, text)
        item.save()

    def getiteminfo(self, uid, key):
        if not self.db:
            return
        item = self.db.find(uid)
        if item:
            try:
                text = item.data[key]
                return text
            except KeyError or AttributeError:
                return

    def updateinfo(self, uid):
        item = self.db.find(uid)
        for view in self.views:
            self.updateview(view, item)

    def updateview(self, view, item):
        try:
            text = item.data[view.name]
        except:
            text = ''
        view.setPlainText(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ItemView()
    w.show()

    sys.exit(app.exec_())


