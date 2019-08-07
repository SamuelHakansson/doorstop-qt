from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .requirementview import RequirementTreeView
from .documentview import DocumentView
from .markreviewedview import MarkReviewedView
from .linkview import LinkView
from .itemview import ItemView
from .itemtestview import ItemTestView
from .itemreqview import ItemReqView

from .databases import ReqDatabase, TestDatabase


class FullView(QSplitter):
    def __init__(self, itemview=None, header=''):
        super().__init__()
        self.itemview = itemview or ItemView()
        self.markdownview = self.itemview.markdownview

        self.attribview = MarkReviewedView()
        self.linkview = LinkView(self.markdownview, self.attribview)

        self.tree = RequirementTreeView(attributeview=self.attribview)
        self.tree.setheaderlabel(header)
        self.docview = DocumentView(header=header + 's')
        self.tree.connectview(self.markdownview)
        self.tree.connectdocview(self.docview)
        self.tree.post_init()
        self.views = [self.attribview, self.linkview, self.docview, self.tree, self.itemview]

        editor = QWidget()
        editorgrid = QVBoxLayout()
        editorgrid.setContentsMargins(0, 0, 0, 0)
        editorgrid.addWidget(self.attribview)
        editorgrid.addLayout(self.itemview)
        editor.setLayout(editorgrid)

        rview = QWidget()
        rviewgrid = QVBoxLayout()
        rview.setLayout(rviewgrid)
        vsplitter = QSplitter(Qt.Vertical)
        vsplitter.addWidget(editor)
        vsplitter.addWidget(self.linkview)
        rviewgrid.addWidget(vsplitter)

        self.addWidget(self.docview)
        self.addWidget(self.tree)
        self.addWidget(rview)

        self.splitterMoved.connect(self.movebuttons)

        self.tree.selectionclb = self.selectfunc
        self.linkview.gotoclb = self.selectfunc
        self.docview.gotoclb = self.selectfunc
        self.tree.setlinkfunc = self.setlink

        self.setstretch()

    def readuid(self, uid):
        if uid is None:
            return
        for view in self.views:
            view.read(uid)

    def selectfunc(self, uid):
        self.readuid(uid)

    def setlink(self, uid):
        return self.linkview.setlinkingitem(uid)

    def movebuttons(self):
        self.tree.setupHeaderwidth()
        self.docview.moverevertbutton()

    def setstretch(self):
        self.setStretchFactor(0, 2)
        self.setStretchFactor(1, 5)
        self.setStretchFactor(2, 4 / self.stretchfac)


class ReqView(FullView):
    def __init__(self):
        self.itemview = ItemReqView()
        self.calldatabase = ReqDatabase
        self.database = None
        self.header = 'Requirement'
        self.stretchfac = 1
        super().__init__(itemview=self.itemview, header=self.header)


class TestView(FullView):
    def __init__(self):
        self.itemview = ItemTestView()
        self.calldatabase = TestDatabase
        self.database = None
        self.header = 'Test'
        self.stretchfac = 2
        super().__init__(itemview=self.itemview, header=self.header)



