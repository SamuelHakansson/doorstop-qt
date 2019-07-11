from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .extratextview import ExtratextView
from .markdownview import MarkdownView
from .icon import Icon
from .lastupdatedtext import LastUpdatedText
from .decisiontakersview import DecisiontakersView
import sys


class ItemView(QVBoxLayout):
    def __init__(self):
        super().__init__()
        self.markdownview = MarkdownView()
        self.decisionlog = ExtratextView('Decision log')
        self.decisiontakers = DecisiontakersView('Decision takers')
        self.lastupdatedtext = LastUpdatedText()
        self.markdownview.name = 'text'
        self.decisionlog.name = 'decisionlog'
        self.decisiontakers.name = 'decisiontakers'
        self.lastupdatedtext.name = 'lastupdated'

        textviewweight = 30
        self.addWidget(self.markdownview, textviewweight)
        self.addWidget(self.decisionlog, 10)
        self.addWidget(self.decisiontakers)
        self.addWidget(self.lastupdatedtext)

        self.views = [self.markdownview, self.decisionlog, self.decisiontakers, self.lastupdatedtext]


        self.decisionlog.textview.selectionChanged.connect(self.vieweditor)
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

        def textChanged():
            if self.currentuid is not None:
                self.cache[self.currentuid]['changed'] = True
                self.savebtn.setVisible(True)
                self.discardbtn.setVisible(True)

        self.markdownview.editview.textChanged.connect(textChanged)
        self.decisionlog.textview.textChanged.connect(textChanged)
        self.decisiontakers.textview.textChanged.connect(textChanged)

        self.decisiontakers.textview.selectionChanged.connect(self.vieweditor)

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
        self.itemfunc = None
        self.readfunc = None

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

    def readtocache(self, view):
        self.cache[self.currentuid][view.name] = view.toPlainText()

    def readfromcache(self, view, uid):
        name = view.name
        if uid in self.cache and name in self.cache[uid]:
                text = self.cache[uid][name]
        else:
            text = self.getiteminfo(uid, name)
        view.setPlainText(text)

    def read(self, uid):
        if self.currentuid is not None:
            if self.currentuid in self.cache and self.cache[self.currentuid]['changed']:
                for view in self.views:
                    self.readtocache(view)

        for view in self.views:
            self.readfromcache(view, uid)

        self.savebtn.setVisible(False)
        self.discardbtn.setVisible(False)
        if uid in self.cache:
            if self.cache[uid]['changed']:
                self.savebtn.setVisible(True)
                self.discardbtn.setVisible(True)
        else:
            self.cache[uid] = {'changed': False}

        self.currentuid = None


        lastupdated = self.getiteminfo(uid, 'lastupdated')
        if lastupdated is None:
            lastupdated = ''
        self.lastupdatedtext.setText('Last updated:' + lastupdated)

        self.currentuid = uid
        self.viewhtml()


    def save(self):
        if self.currentuid is None:
            return
        if self.currentuid not in self.cache:
            return
        self.savefunc(self.currentuid)
        self.cache[self.currentuid]['changed'] = False

        for view in self.views:
            name = view.name
            if name in self.cache[self.currentuid]:
                del self.cache[self.currentuid][name]
        self.updateinfo(self.currentuid)
        self.savebtn.setVisible(False)
        self.discardbtn.setVisible(False)

    def savefunc(self, uid):
        for view in self.views:
            self.saveview(view, uid)


    def saveview(self, view, uid):
        text = view.text()
        item = self.itemfunc(uid)
        item.set(view.name, text)
        item.save()

    def getiteminfo(self, uid, key):
        item = self.itemfunc(uid)
        try:
            text = item._data[key]
            return text
        except KeyError:
            return

    def updateinfo(self, uid):
        item = self.itemfunc(uid)
        for view in self.views:
            self.updateview(view, item)

    def updateview(self, view, item):
        try:
            text = item._data[view.name]
        except:
            text = ''
        view.setPlainText(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ItemView()
    w.show()

    sys.exit(app.exec_())


