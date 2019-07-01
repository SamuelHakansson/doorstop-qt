#!/usr/bin/env python

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .markdownview import MarkdownView
import doorstop
from .documentview import DocumentTreeView
from .createcatdiag import CreateCategoryDialog
from .editcatdiag import EditCategoryDialog
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



def main():
    import sys
    import datetime
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)


    splitter = QSplitter()
    splitter.resize(1024, 768)
    splitter.setWindowTitle('doorstop-qt {}'.format(VERSION))

    v = MarkdownView()
    createcatdiag = CreateCategoryDialog()

    attribview = AttributeView()
    linkview = LinkView(v)

    tree = DocumentTreeView(attributeview=attribview)
    editcatdiag = EditCategoryDialog(tree.catselector)
    tree.connectview(v)
    tree.connecteditcatdiag(editcatdiag)
    tree.connectcreatecatdiag(createcatdiag)
    tree.post_init()
    def selectfunc(uid):
        if uid is None:
            return
        attribview.read(uid)
        linkview.read(uid)
        v.read(uid)
        tree.read(uid)

    def setlink(uid):
        return linkview.setlinkingitem(uid)

    tree.selectionclb = selectfunc
    linkview.gotoclb = selectfunc
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
    v.readfunc = lambda uid: db.find(uid).text
    v.itemfunc = lambda uid: db.find(uid)

    def savefunc(uid, text):
        item = db.find(uid)
        item.text = text
        item._data['lastupdated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        item.save()
        tree.updateuid(uid)

    v.savefunc = savefunc
    db.add_listeners([tree, editcatdiag, createcatdiag])

    def modeclb(editmode):
        if editmode:
            attribview.showref(True)
        else:
            attribview.showref(False)
    v.modeclb = modeclb



    editor = QWidget()
    editorgrid = QVBoxLayout()
    editorgrid.setContentsMargins(0, 0, 0, 0)
    editorgrid.addWidget(attribview)
    editorgrid.addWidget(v)
    editor.setLayout(editorgrid)

    rview = QWidget()
    rviewgrid = QVBoxLayout()
    rview.setLayout(rviewgrid)
    vsplitter = QSplitter(Qt.Vertical)
    vsplitter.addWidget(editor)
    vsplitter.addWidget(linkview)
    vsplitter.setStretchFactor(0, 100)
    rviewgrid.addWidget(vsplitter)

    splitter.addWidget(tree)
    splitter.addWidget(rview)
    splitter.setStretchFactor(100, 1)



    splitter.show()

    sys.exit(app.exec_())
