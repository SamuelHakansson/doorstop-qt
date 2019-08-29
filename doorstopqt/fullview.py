from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .itemtreeview import ItemTreeView
from .documentview import DocumentView
from .markreviewedview import MarkReviewedView
from .linkview import LinkView
from .linkotherview import LinkOtherView
from .itemtestview import ItemTestView
from .itemreqview import ItemReqView

from .databases import OtherDatabase

'''
Each of the views (requirement, test, and product view) is a fullview. 
'''


class FullView(QSplitter):
    def __init__(self):
        super().__init__()
        self.markdownview = self.itemview.markdownview
        self.attribview = MarkReviewedView(self.publishtest)
        self.linkview = LinkView(self.itemview, self.attribview, header=self.header.lower())
        self.linkotherview = LinkOtherView(self.itemview, self.attribview, self.keys[0], self.ownkey,
                                           header=self.otherheaders[0].lower())
        self.linkotherview2 = LinkOtherView(self.itemview, self.attribview, self.keys[1], self.ownkey,
                                            header=self.otherheaders[1].lower(),
                                            changeexpectedresults=self.changeexpectedresults)
        self.linkviews = [self.linkview, self.linkotherview, self.linkotherview2]

        self.tree = ItemTreeView(attributeview=self.attribview)
        self.tree.setheaderlabel(self.header)
        self.docview = DocumentView(header=self.header + 's')
        self.tree.connectview(self.markdownview)
        self.tree.connectdocview(self.docview)
        self.tree.post_init()
        self.views = [self.attribview, self.linkview, self.linkotherview, self.linkotherview2, self.docview, self.tree, self.itemview]

        editor = QWidget()
        editorgrid = QVBoxLayout()
        editorgrid.setContentsMargins(0, 0, 0, 0)
        editorgrid.addWidget(self.itemview)
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
        rightvsplitter.addWidget(self.linkotherview)
        rightvsplitter.addWidget(self.linkotherview2)
        rlinkviewgrid.addWidget(rightvsplitter)

        self.addWidget(self.docview)
        self.addWidget(self.tree)
        self.addWidget(rview)
        self.addWidget(rlinkview)

        self.splitterMoved.connect(self.movebuttons)

        self.tree.selectionclb = self.selectfunc
        self.linkview.gotoclb = self.selectfunc
        self.linkotherview.gotoclb = self.selectfunc
        self.linkotherview2.gotoclb = self.selectfunc
        self.docview.gotoclb = self.selectfunc
        self.tree.setlinkfunc = self.setlink

        self.tree.otherdbviews = [self.linkotherview, self.linkotherview2]
        self.attribview.readlinkview = self.linkview.read
        self.setstretch()

        self.currentuid = None
        self.markdownview.modeclb = self.modeclb

    def modeclb(self, editmode):
        if editmode:
            self.attribview.showref(True)
        else:
            self.attribview.showref(False)

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
        self.docview.searchlayout.moveclearbutton()
        for lw in self.linkviews:
            lw.linkentry.moveclearbutton()

    def setstretch(self):
        self.setStretchFactor(0, 2)
        self.setStretchFactor(1, 4)
        self.setStretchFactor(2, int(6 / self.stretchfac))
        self.setStretchFactor(3, 4)


REQUIREMENT = 'requirement'
TEST = 'test'
PRODUCT = 'product'
LINKEDREQUIREMENTS = 'linkedrequirements'
LINKEDTESTS = 'linkedtests'
LINKEDPRODUCTS = 'linkedproducts'


class ReqView(FullView):
    def __init__(self):
        self.itemview = ItemReqView()
        self.calldatabase = OtherDatabase
        self.database = None
        self.header = 'Requirement'
        self.otherheaders = [TEST, PRODUCT]
        self.keys = [LINKEDTESTS, LINKEDPRODUCTS]
        self.ownkey = LINKEDREQUIREMENTS
        self.stretchfac = 2
        self.publishtest = False
        self.changeexpectedresults = False
        super().__init__()


class TestView(FullView):
    def __init__(self):
        self.itemview = ItemTestView()
        self.itemview.vartables.inputtable.table.setHorizontalHeaderLabels(['Name', 'Default value'])
        self.itemview.vartables.expectedresultsmarkdownview.label.setText('Default expected results')
        self.calldatabase = OtherDatabase
        self.database = None
        self.header = 'Test'
        self.otherheaders = [REQUIREMENT, PRODUCT]
        self.keys = [LINKEDREQUIREMENTS, LINKEDPRODUCTS]
        self.ownkey = LINKEDTESTS
        self.stretchfac = 2
        self.publishtest = False
        self.changeexpectedresults = False
        super().__init__()


class ProductView(FullView):
    def __init__(self):
        self.itemview = ItemTestView()
        self.calldatabase = OtherDatabase
        self.database = None
        self.header = 'Product'
        self.otherheaders = [REQUIREMENT, TEST]
        self.keys = [LINKEDREQUIREMENTS, LINKEDTESTS]
        self.ownkey = LINKEDPRODUCTS
        self.stretchfac = 2
        self.publishtest = True
        self.changeexpectedresults = True
        super().__init__()

    def publishalltestsforallproducts(self):
        for document in self.database.root.documents:
            for item in document.items:
                tree, items, uid = self.linkotherview2.getpublishtree(item.uid)
                if items:
                    self.attribview.publishtestdoc(tree, items, str(uid))


