from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from .markdownview import MarkdownView, MarkdownViewExt
from .icon import Icon
import sys


class ItemView(QSplitter):
    def __init__(self, views=None, viewssplitted=None):
        super().__init__()
        self.setOrientation(Qt.Vertical)
        self.db = None
        self.markdownview = MarkdownView()
        self.markdownview.name = 'text'
        self.views = [self.markdownview] + (views or [])
        for view in self.views:
            self.addWidget(view)
        if viewssplitted:
            self.views = [self.markdownview] + (viewssplitted or [])
        self.currentuid = None
        self.markdownviews = [self.markdownview]
        for view in viewssplitted:
            if type(view) is MarkdownView or type(view) is MarkdownViewExt:
                self.markdownviews.append(view)

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

        for markdownview in self.markdownviews:
            markdownview.editview.textChanged.connect(self.textChanged)
            markdownview.htmlview.selectionChanged.connect(self.vieweditor)

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
        self.applytootheritem = None

    def connectdb(self, db):
        self.db = db
        self.read(self.currentuid)
        for view in self.markdownviews:
            view.connectdb(db)

    def textChanged(self):
        if self.currentuid is not None:
            print('cache', flush=True)
            self.cache[self.currentuid][self.CHANGED] = True
            self.savebtn.setVisible(True)
            self.discardbtn.setVisible(True)

    def viewhtml(self):
        for mv in self.markdownviews:
            mv.viewhtml()
        self.editbtn.setVisible(True)
        self.previewbtn.setVisible(False)

    def vieweditor(self):
        for mv in self.markdownviews:
            mv.vieweditor()
        self.previewbtn.setVisible(True)
        self.editbtn.setVisible(False)

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
            if self.applytootheritem:
                self.applytootheritem(uid)

    def saveview(self, view, uid):
        text = view.text()
        item = self.db.find(uid)
        if view.name == 'expectedresults':
            if 'expectedresults' in item.data:
                if text[0][0] in [x[0] for x in item.data['expectedresults']]:
                    newdata = item.data['expectedresults']
                    for i, pair in enumerate(newdata):
                        if pair[0] == text[0][0]:
                            del newdata[i]
                            newdata.insert(i, text[0])
                    text = newdata

                else:
                    text = item.data['expectedresults'] + text
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

    def updatelastupdated(self):
        for view in self.views:
            if view.name == 'lastupdated':
                view.setPlainText(view.toPlainText())

    def updateexpectedresults(self, uid):
        for view in self.views:
            if view.name == 'expectedresults':
                #view.vieweditor()
                view.updatetitle(uid)
                item = self.db.find(self.currentuid)
                text = None
                if 'expectedresults' in item.data:
                    for pair in item.data['expectedresults']:
                        if pair[0] == uid:
                            text = [pair]
                print('about to set text', flush=True)
                view.editview.blockSignals(True)
                view.setPlainText(text)
                view.editview.blockSignals(False)
                print('text set', flush=True)


                self.viewhtml()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ItemView()
    w.show()

    sys.exit(app.exec_())


