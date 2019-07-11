#!/usr/bin/env python

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .markdownview import MarkdownView
import doorstop
from .requirementview import RequirementTreeView
from .documentview import DocumentView
from .attributeview import AttributeView
from .linkview import LinkView
from .version import VERSION
import resources # resources fetches icons

class ReqDatabase(object):
    def __init__(self):
        self.listeners = []
        self.root = None
        self.reload()

    def add_listeners(self, l):
        if type(l) is list:
            for listener in l:
                listener.connectdb(self)
                self.listeners.append(listener)
        else:
            l.connectdb(self)
            self.listeners.append(l)

    def reload(self):
        self.root = doorstop.core.builder.build()
        for l in self.listeners:
            l.connectdb(self)

    def find(self, uid):
        for document in self.root:
            for item in document:
                if str(item.uid) == uid:
                    return item
        return None

    def remove(self, uid):
        item = self.find(uid)
        item.delete()
        self.reload()


class CustomSplitter(QSplitter):
    def __init__(self):
        super(CustomSplitter, self).__init__()
        self.movebuttons = None

    def resizeEvent(self, a0: QResizeEvent) -> None:
        if self.movebuttons:
            self.movebuttons()
        super().resizeEvent(a0)


def main():
    import sys

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    splitter = CustomSplitter()

    screen_resolution = app.desktop().screenGeometry()
    screenwidth, screenheight = screen_resolution.width(), screen_resolution.height()
    width = int(screenwidth*11/16)
    height = int(screenheight*11/16)
    splitter.resize(width, height)

    splitter.setWindowTitle('doorstop-qt {}'.format(VERSION))

    markdownview = MarkdownView()

    attribview = AttributeView()
    linkview = LinkView(markdownview, attribview)

    tree = RequirementTreeView(attributeview=attribview)
    docview = DocumentView()
    tree.connectview(markdownview)
    tree.connectdocview(docview)
    tree.post_init()
    def selectfunc(uid):
        if uid is None:
            return
        attribview.read(uid)
        linkview.read(uid)
        markdownview.read(uid)
        tree.read(uid)
        docview.read(uid)


    def setlink(uid):
        return linkview.setlinkingitem(uid)

    tree.selectionclb = selectfunc
    linkview.gotoclb = selectfunc
    docview.gotoclb = selectfunc
    tree.setlinkfunc = setlink

    tree.clipboard = lambda x: app.clipboard().setText(x)

    has_started = False
    while not has_started:
        try:
            db = ReqDatabase()
            has_started = True
        except:
            import os
            f = str(QFileDialog.getExistingDirectory(None, "Select Directory"))
            if not os.path.isdir(f):
                f = os.path.dirname(f)
            os.chdir(f)
    db.add_listeners([attribview, linkview])
    markdownview.readfunc = lambda uid: db.find(uid).text
    markdownview.itemfunc = lambda uid: db.find(uid)

    db.add_listeners([tree, docview])

    def modeclb(editmode):
        if editmode:
            attribview.showref(True)
        else:
            attribview.showref(False)
    markdownview.modeclb = modeclb


    def movebuttons():
        tree.setupHeaderwidth()
        docview.moverevertbutton()

    splitter.movebuttons = movebuttons

    editor = QWidget()
    editorgrid = QVBoxLayout()
    editorgrid.setContentsMargins(0, 0, 0, 0)
    editorgrid.addWidget(attribview)
    editorgrid.addWidget(markdownview)
    editor.setLayout(editorgrid)

    rview = QWidget()
    rviewgrid = QVBoxLayout()
    rview.setLayout(rviewgrid)
    vsplitter = QSplitter(Qt.Vertical)
    vsplitter.addWidget(editor)
    vsplitter.addWidget(linkview)
    rviewgrid.addWidget(vsplitter)

    splitter.addWidget(docview)
    splitter.addWidget(tree)
    splitter.addWidget(rview)
    splitter.splitterMoved.connect(movebuttons)
    splitter.setStretchFactor(0, 2)
    splitter.setStretchFactor(1, 5)
    splitter.setStretchFactor(2, 4)

    splitter.show()
    tree.setupHeaderwidth()

    sys.exit(app.exec_())
