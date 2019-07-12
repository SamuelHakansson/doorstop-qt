#!/usr/bin/env python

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import doorstop
from .requirementview import RequirementTreeView
from .documentview import DocumentView
from .attributeview import AttributeView
from .linkview import LinkView
from .itemview import ItemView
from .itemtestview import ItemTestView
from .version import VERSION
import os
from pathlib import Path
from .itemreqview import ItemReqView
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


class TestDatabase(ReqDatabase):
    def __init__(self):
        currentdir = os.getcwd()
        os.chdir("..")
        self.folder = '/tests/'
        self.path = Path(os.getcwd()+self.folder)
        super().__init__()
        os.chdir(currentdir)

    def reload(self):
        self.root = doorstop.core.builder.build(root=self.path)
        for l in self.listeners:
            l.connectdb(self)



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
    width = int(screenwidth*13/16)
    height = int(screenheight*13/16)
    splitter.resize(width, height)

    splitter.setWindowTitle('doorstop-qt {}'.format(VERSION))
    itemview = ItemReqView()
    markdownview = itemview.markdownview

    attribview = AttributeView()
    linkview = LinkView(markdownview, attribview)

    tree = RequirementTreeView(attributeview=attribview)
    docview = DocumentView()
    tree.connectview(markdownview)
    tree.connectdocview(docview)
    tree.post_init()

    def readuid(views, uid):
        if uid is None:
            return
        for view in views:
            view.read(uid)

    def selectfunc(uid):
        views = [attribview, linkview, itemview, tree, docview]
        readuid(views, uid)

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
    itemview.readfunc = lambda uid: db.find(uid).text
    itemview.itemfunc = lambda uid: db.find(uid)

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
    editorgrid.addLayout(itemview)
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

    def setuptestviews(testdb):

        testattrview = AttributeView()
        testdocview = DocumentView()
        testtree = RequirementTreeView(attributeview=testattrview)
        testmarkdown = ItemTestView()
        testtree.setheaderlabel('Test')
        testtree.connectview(testmarkdown)
        testtree.connectdocview(testdocview)
        testtree.post_init()

        def testselectfunc(uid):
            views = [testtree, testdocview, testattrview, testmarkdown]
            readuid(views, uid)

        testtree.selectionclb = testselectfunc
        testdocview.gotoclb = testselectfunc

        testdb.add_listeners([testattrview])

        testmarkdown.readfunc = lambda uid: db.find(uid).text
        testmarkdown.itemfunc = lambda uid: db.find(uid)

        testdb.add_listeners([testdocview, testtree])

        testtree.clipboard = lambda x: app.clipboard().setText(x)

        testsplitter = QSplitter(Qt.Horizontal)
        testsplitter.addWidget(testdocview)
        testsplitter.addWidget(testtree)

        editor = QWidget()
        editorgrid = QVBoxLayout()
        editorgrid.setContentsMargins(0, 0, 0, 0)
        editorgrid.addLayout(testmarkdown)
        editor.setLayout(editorgrid)
        testsplitter.addWidget(editor)

        splitter.addWidget(testsplitter)

    try:
        testdb = TestDatabase()
    except:
        pass

    setuptestviews(testdb)
    splitter.show()
    tree.setupHeaderwidth()

    sys.exit(app.exec_())
