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

from .databases import ReqDatabase, TestDatabase, ProductDatabase


class FullView(QSplitter):
    def __init__(self):
        super().__init__()
        self.markdownview = self.itemview.markdownview

        self.attribview = MarkReviewedView(self.publishtest)
        self.linkview = LinkView(self.markdownview, self.attribview, header=self.header.lower())
        self.reqtestlinkview = LinkReqAndTestView(self.markdownview, self.attribview, self.keys[0],  header=self.otherheaders[0].lower())
        self.reqtestlinkview2 = LinkReqAndTestView(self.markdownview, self.attribview, self.keys[1],  header=self.otherheaders[1].lower())

        self.tree = RequirementTreeView(attributeview=self.attribview)
        self.tree.setheaderlabel(self.header)
        self.docview = DocumentView(header=self.header + 's')
        self.tree.connectview(self.markdownview)
        self.tree.connectdocview(self.docview)
        self.tree.post_init()
        self.views = [self.attribview, self.linkview, self.reqtestlinkview, self.reqtestlinkview2,  self.docview, self.tree, self.itemview]

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
        rightvsplitter.addWidget(self.reqtestlinkview2)
        rlinkviewgrid.addWidget(rightvsplitter)

        self.addWidget(self.docview)
        self.addWidget(self.tree)
        self.addWidget(rview)
        self.addWidget(rlinkview)

        self.splitterMoved.connect(self.movebuttons)

        self.tree.selectionclb = self.selectfunc
        self.linkview.gotoclb = self.selectfunc
        self.reqtestlinkview.gotoclb = self.selectfunc
        self.reqtestlinkview2.gotoclb = self.selectfunc
        self.docview.gotoclb = self.selectfunc
        self.tree.setlinkfunc = self.setlink

        self.tree.otherdbviews = [self.reqtestlinkview, self.reqtestlinkview2]

        self.setstretch()

        self.currentuid = None

    def readuid(self, uid, readcurrent=False):
        if uid is None and readcurrent is False:
            return
        if readcurrent:
            uid = self.currentuid
        for view in self.views:
            view.read(uid)
        self.currentuid = uid

    def selectfunc(self, uid, readcurrent=False):
        self.readuid(uid, readcurrent)

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
        self.otherheaders = ['test', 'product']
        self.keys = ['linkedtests', 'linkedproducts']
        self.stretchfac = 2
        self.publishtest = False
        super().__init__()


class TestView(FullView):
    def __init__(self):
        self.itemview = ItemTestView()
        self.calldatabase = TestDatabase
        self.database = None
        self.header = 'Test'
        self.otherheaders = ['requirement', 'product']
        self.keys = ['linkedrequirements', 'linkedproducts']
        self.stretchfac = 2
        self.publishtest = False
        super().__init__()


class ProductView(FullView):
    def __init__(self):
        self.itemview = ItemTestView()
        self.calldatabase = ProductDatabase
        self.database = None
        self.header = 'Product'
        self.otherheaders = ['requirement', 'test']
        self.keys = ['linkedrequirements', 'linkedtests']
        self.stretchfac = 2
        self.publishtest = True
        super().__init__()


