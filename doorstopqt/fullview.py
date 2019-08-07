from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .requirementview import RequirementTreeView
from .documentview import DocumentView
from .markreviewedview import MarkReviewedView
from .linkview import LinkView
from .linkreqandtestview import LinkReqAndTestView
from .itemtestview import ItemTestView
from .itemreqview import ItemReqView

from .databases import ReqDatabase, TestDatabase


class FullView(QSplitter):
    def __init__(self):
        super().__init__()
        self.markdownview = self.itemview.markdownview

        self.attribview = MarkReviewedView()
        self.linkview = LinkView(self.markdownview, self.attribview, header=self.header.lower()+"s")
        self.reqtestlinkview = LinkReqAndTestView(self.markdownview, self.attribview, header=self.otherheader.lower()+"s")

        self.tree = RequirementTreeView(attributeview=self.attribview)
        self.tree.setheaderlabel(self.header)
        self.docview = DocumentView(header=self.header + 's')
        self.tree.connectview(self.markdownview)
        self.tree.connectdocview(self.docview)
        self.tree.post_init()
        self.views = [self.attribview, self.linkview, self.reqtestlinkview, self.docview, self.tree, self.itemview]

        editor = QWidget()
        editorgrid = QVBoxLayout()
        editorgrid.setContentsMargins(0, 0, 0, 0)
        editorgrid.addLayout(self.itemview)
        editor.setLayout(editorgrid)

        rview = QWidget()
        rviewgrid = QVBoxLayout()
        rview.setLayout(rviewgrid)
        vsplitter = QSplitter(Qt.Vertical)
        vsplitter.addWidget(editor)
        rviewgrid.addWidget(vsplitter)

        rlinkview = QWidget()
        rlinkviewgrid = QVBoxLayout()
        rlinkview.setLayout(rlinkviewgrid)

        rightvsplitter = QSplitter(Qt.Vertical)
        rightvsplitter.addWidget(self.attribview)
        rightvsplitter.addWidget(self.linkview)
        rightvsplitter.addWidget(self.reqtestlinkview)
        rlinkviewgrid.addWidget(rightvsplitter)

        self.addWidget(self.docview)
        self.addWidget(self.tree)
        self.addWidget(rview)
        self.addWidget(rlinkview)

        self.splitterMoved.connect(self.movebuttons)

        self.tree.selectionclb = self.selectfunc
        self.linkview.gotoclb = self.selectfunc
        self.reqtestlinkview.gotoclb = self.selectfunc
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
        self.setStretchFactor(1, 3)
        self.setStretchFactor(2, int(4 / self.stretchfac))
        self.setStretchFactor(3, 3)


class ReqView(FullView):
    def __init__(self):
        self.itemview = ItemReqView()
        self.calldatabase = ReqDatabase
        self.database = None
        self.header = 'Requirement'
        self.otherheader = 'test'
        self.stretchfac = 1
        super().__init__()


class TestView(FullView):
    def __init__(self):
        self.itemview = ItemTestView()
        self.calldatabase = TestDatabase
        self.database = None
        self.header = 'Test'
        self.otherheader = 'requirement'
        self.stretchfac = 2
        super().__init__()



