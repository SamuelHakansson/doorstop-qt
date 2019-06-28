from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from doorstop import Tree

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

        self.tree.setModel(self.model)

        self.apply.clicked.connect(self.onapply)
        self.model.layoutChanged.connect(self.onlayoutchanged)
        self.vbox.addWidget(self.apply)
        self.tree.setMinimumSize(self.tree.width()/2, self.tree.height())

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.contextmenu)

        self.model.itemChanged.connect(self.namechanged)

        self.documentstodelete = []
        self.namechangeditems = []
        self.doctonewname = {}

    def namechanged(self, changeditem):
        self.namechangeditems.append(changeditem)

    def setnewnames(self):
        for changeditem in self.namechangeditems:
            cat = changeditem.data(Qt.UserRole)
            newname = changeditem.text()
            self.doctonewname[str(cat)] = newname

            changeditem.setText(newname)
            changeddoc = self.docsdict[cat]
            newname.replace(" ", "_")
            changeddoc.prefix = newname
            children = self.findallchildren(changeditem)
            if children:
                for child in children:
                    childdoc = self.docsdict[child.text()]
                    childdoc.parent = newname
            self.model.blockSignals(True)
            changeditem.setData(newname, role=Qt.UserRole)
            self.model.blockSignals(False)
            self.docsdict[newname] = changeddoc
            del self.docsdict[str(cat)]
        self.namechangeditems = []

    def show(self):
        super(EditCategoryDialog, self).show()

    def connectdb(self, db):
        self.db = db
        self.catsel.connectdb(db)
        self.docs = [x for x in self.db.root]
        self.docsdict = {}
        for d in self.docs:
            self.docsdict[str(d)] = d
        self.model.blockSignals(True)
        self.buildlist()
        self.model.blockSignals(False)

    def contextmenu(self, pos):
        menu = QMenu(parent=self.tree)
        act = menu.addAction('Remove category')
        si = self.tree.selectedIndexes()
        indextoremove = si[0]
        itemtoremove = self.model.itemFromIndex(indextoremove)
        def documenttoremove(itemtoremove):
            data = itemtoremove.data(Qt.UserRole)
            itemtoremove.setBackground(QBrush(QColor("red")))
            self.documentstodelete.append(data)
            children = self.findallchildren(itemtoremove)
            if children:
                for child in children:
                    documenttoremove(child)

        act.triggered.connect(lambda: documenttoremove(itemtoremove))
        menu.popup(self.tree.mapToGlobal(pos))


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

    def onapply(self):
        self.setnewnames()
        self.changehierarchy()
        self.db.reload()
        self.hide()


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
            if category.parent != pardata:
                if pardata is not None:
                    category.parent = pardata
                else:
                    category._data['parent'] = None
                    category.save()

        self.deletependingdocuments()
        current_category = self.catsel.text()
        if current_category not in self.docsdict:

            somecategory = self.docsdict[list(self.docsdict.keys())[0]]
            self.catsel.select(str(somecategory))
        self.documentstodelete = []

    def deletependingdocuments(self):
        if len(self.documentstodelete) == 0:
            return
        for data in self.documentstodelete:
            self.docsdict[str(data)].delete()
            del self.docsdict[str(data)]


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

    def findallchildren(self, item):
        if not item.hasChildren():
            return
        rows = item.rowCount()
        children = []
        for i in range(rows):
            child = item.child(i, 0)
            if child is not None:
                children.append(child)
        return children



