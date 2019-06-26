from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from doorstop import Tree, Document

class EditCategoryDialog(QDialog):
    def __init__(self, catselector, parent=None):
        super(EditCategoryDialog, self).__init__(parent)

        self.setWindowTitle('Edit category hierarchy')
        self.vbox = QVBoxLayout()
        grid = QGridLayout()
        self.catsel = catselector
        self.model = QStandardItemModel()

        self.tree = QTreeView()
        self.tree.header().hide()
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.setIndentation(20)
        self.tree.setAlternatingRowColors(True)

        grid.addWidget(QLabel('Categories:'), 0, 1)
        grid.addWidget(self.tree, 1, 1)
        self.warningmessage = QLabel('Warning: only one root allowed')
        self.warningmessage.setStyleSheet('color: red')
        grid.addWidget(self.warningmessage, 3, 1)
        self.warningmessage.hide()
        self.apply = QPushButton('Apply')
        self.db = None

        g = QWidget()
        g.setLayout(grid)
        self.vbox.addWidget(g)
        self.setLayout(self.vbox)

        self.undostack = QUndoStack()
        self.tree.setModel(self.model)

        self.apply.clicked.connect(self.changehierarchy)
        self.model.layoutChanged.connect(self.onlayoutchanged)
        self.vbox.addWidget(self.apply)

    def applytreechange(self):
        self.db.root = Tree.from_list(self.docs, self.db.root.root)
        self.catsel.buildlist()
        self.hide()

    def show(self):
        super(EditCategoryDialog, self).show()

    def connectdb(self, db):
        self.db = db
        self.catsel.connectdb(db)
        self.docs = [x for x in self.db.root]
        self.docsdict = {}
        for d in self.docs:
            self.docsdict[str(d)] = d
        self.buildlist()


    def buildlist(self):
        if self.db is None or len(self.db.root.documents) == 0:
            return
        self.model.clear()
        self.createhierarchy()

    def createhierarchy(self):
        graph = self.db.root.draw().split('\n')
        graph = filter(lambda s: any([c.isalnum() for c in s]), graph)
        prevpos = 0
        items = {}
        previtem = None

        for g in graph:
            item = QStandardItem()
            pos = 0
            for i, x in enumerate(g):
                if x.isalpha():
                    pos = i
                    break
            if pos == 0:
                self.model.appendRow(item)
            elif pos < prevpos:
                prevlvlitem = items[pos-4][-1]
                prevlvlitem.appendRow(item)
            elif pos == prevpos:
                previtem.parent().appendRow(item)
            else:
                previtem.appendRow(item)
            if pos in items:
                items[pos].append(item)
            else:
                items[pos] = [item]
            gtext = str(g[pos:])
            item.setData(gtext, role=Qt.UserRole)
            item.setText(gtext)
            prevpos = pos
            previtem = item
        self.tree.expandAll()

    def changehierarchy(self):
        movedobject = self.tree.currentIndex()

        nextlist = self.getnext(movedobject, [])
        previouslist = self.getprevious(movedobject, [])
        currentobjects_list = previouslist + [movedobject] + nextlist
        nrroots = 0
        for obj in currentobjects_list:
            parindex = obj.parent()
            pardata = self.model.data(parindex, role=Qt.UserRole)
            if pardata == None:
                nrroots += 1
        if nrroots != 1:
            return

        for obj in currentobjects_list:
            data = self.model.data(obj, role=Qt.UserRole)
            parindex = obj.parent()

            pardata = self.model.data(parindex, role=Qt.UserRole)
            category = self.docsdict[data]
            if pardata != None:
                category.parent = pardata
            else:
                category._data['parent'] = None
                category.save()
        self.applytreechange()

    def onlayoutchanged(self):
        movedobject = self.tree.currentIndex()

        nextlist = self.getnext(movedobject, [])
        previouslist = self.getprevious(movedobject, [])
        currentobjects_list = previouslist + nextlist

        nrroots = 0
        for obj in currentobjects_list:
            parindex = obj.parent()
            pardata = self.model.data(parindex, role=Qt.UserRole)
            if pardata == None:
                nrroots += 1
        if nrroots != 1:
            self.warningmessage.show()
            self.apply.setDisabled(True)
        else:
            self.warningmessage.hide()
            self.apply.setDisabled(False)
        self.tree.expandAll()

    def getnext(self, index, nextobjectslist):
        nextobject = self.tree.indexBelow(index)
        data = self.model.data(nextobject, role=Qt.UserRole)
        if data is not None:
            nextobjectslist.append(nextobject)
            self.getnext(nextobject, nextobjectslist)
        return nextobjectslist

    def getprevious(self, index, nextobjectslist):
        previousobject = self.tree.indexAbove(index)
        data = self.model.data(previousobject, role=Qt.UserRole)
        if data is not None:
            nextobjectslist.insert(0, previousobject)
            self.getprevious(previousobject, nextobjectslist)
        return nextobjectslist



