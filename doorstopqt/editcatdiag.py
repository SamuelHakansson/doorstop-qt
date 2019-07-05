from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .customcompleter import CustomQCompleter

class EditCategoryDialog(QWidget):
    def __init__(self, parent=None):
        super(EditCategoryDialog, self).__init__(parent)

        self.vbox = QVBoxLayout()
        grid = QVBoxLayout()
        self.model = QStandardItemModel()

        self.tree = QTreeView()
        self.tree.header().hide()
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.setIndentation(20)
        self.tree.setAlternatingRowColors(True)

        grid.addWidget(self.tree)

        self.warningmessage = QLabel('Warning: only one root allowed')
        self.warningmessage.setStyleSheet('color: red')
        grid.addWidget(self.warningmessage)
        self.warningmessage.hide()

        self.removemessage = QLabel('Sub document will be removed if its parent is removed')
        self.removemessage.setStyleSheet('color: red')
        grid.addWidget(self.removemessage)
        self.removemessage.hide()


        self.apply = QPushButton('Apply')
        self.apply.hide()
        self.revert = QPushButton('Revert')
        self.revert.hide()

        papirusicons = QIcon()
        papirusicons.setThemeName('Papirus')
        searchicon = papirusicons.fromTheme("search")
        clearicon = papirusicons.fromTheme("edit-clear-all")

        self.db = None

        #g = QWidget()
        #g.setLayout(grid)
        #self.vbox.addWidget(g)
        self.searchbox = QLineEdit()
        self.searchbox.setStyleSheet("background-color: white; border: 0px;")
        self.searchlabel = QLabel()
        self.searchlabel.setStyleSheet("background-color: white")
        self.searchlabel.setPixmap(searchicon.pixmap(16, 16))
        self.clearbutton = QPushButton(clearicon, '')
        self.clearbutton.setStyleSheet("background-color: white; border: 0px;")
        self.searchlayout = QHBoxLayout()
        self.searchlayout.addWidget(self.searchlabel)
        self.searchlayout.addWidget(self.searchbox)
        self.searchlayout.addWidget(self.clearbutton)
        self.searchlayout.setSpacing(0)
        self.completer = CustomQCompleter()
        self.searchbox.setCompleter(self.completer)
        self.vbox.addLayout(self.searchlayout)
        self.vbox.addWidget(self.tree)
        self.setLayout(self.vbox)

        self.tree.setModel(self.model)

        self.apply.clicked.connect(self.onapply)
        self.revert.clicked.connect(self.onrevert)
        self.model.layoutChanged.connect(self.onlayoutchanged)
        self.hbox = QHBoxLayout()

        self.hbox.addWidget(self.revert)
        self.hbox.addWidget(self.apply)
        self.vbox.addLayout(self.hbox)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.contextmenu)

        self.model.itemChanged.connect(self.namechanged)
        self.documentstodelete = []
        self.namechangeditems = []
        self.doctonewname = {}
        self.willberemoved = {}
        self.categoriestocreate = []
        self.path = './reqs/'
        self.badcharacters = ['<', '>', ':', '/', '\\', '|', '?', '*']
        self.gotoclb = None
        self.completer.activated.connect(self.gotocompleted)
        self.clearbutton.clicked.connect(self.clearsearchbox)

    def clearsearchbox(self):
        self.searchbox.setText('')

    def updateCompleter(self):
        docs = list(map(lambda x: x, self.db.root.documents))
        texts = []

        start = '**Feature name:**'
        end = "**Feature requirement:**"
        self.completerdict = {}
        for doc in docs:
            for item in doc.items:
                dt = item.text
                if start in dt and end in dt:
                    text = dt[dt.find(start) + len(start):dt.rfind(end)].strip()
                    texts.append(text)
                    self.completerdict[text] = item.uid
        model = QStringListModel()
        model.setStringList(texts)
        self.completer.setModel(model)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)

    def goto(self, uid):
        if self.gotoclb:
            self.gotoclb(uid)

    def gotocompleted(self, searchstr):
        uid = self.completerdict[searchstr]
        self.goto(uid)

    def namechanged(self, changeditem):
        self.namechangeditems.append(changeditem)
        self.setnewnames()

    def setnewnames(self): #  uses a list to be able to use an apply button
        for changeditem in self.namechangeditems:
            cat = changeditem.data(Qt.UserRole)
            newname = changeditem.text()

            if cat:
                if cat != newname:
                    newname.replace(" ", "_")
                    self.doctonewname[str(cat)] = newname
                    changeditem.setText(newname)

                    changeddoc = self.docsdict[str(cat)]
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
            else:
                self.categoriestocreate.append(changeditem)


        self.namechangeditems = []

        self.createnew()

    def show(self):
        super(EditCategoryDialog, self).show()
        self.raise_()

    def connectdb(self, db):
        self.db = db
        self.docs = [x for x in self.db.root]
        self.docsdict = {}
        for d in self.docs:
            self.docsdict[str(d)] = d
        self.model.blockSignals(True)
        self.buildlist()
        self.model.blockSignals(False)
        self.updateCompleter()

    def contextmenu(self, pos):
        menu = QMenu(parent=self.tree)
        index = self.tree.indexAt(pos)
        data = self.model.data(index)
        addaction = menu.addAction("Create child document")
        addaction.triggered.connect(lambda: addnewdocument(item))
        menu.addSeparator()
        renameaction = menu.addAction("Rename")
        renameaction.triggered.connect(lambda: rename(item))
        menu.addSeparator()
        if data not in self.willberemoved:
            removeaction = menu.addAction('Remove')
            removeaction.triggered.connect(lambda: documenttoremove(item))
        else:
            notremoveaction = menu.addAction('Do not remove')
            notremoveaction.triggered.connect(lambda: documenttonotremove(item))

        si = self.tree.selectedIndexes()
        indextoremove = si[0]
        item = self.model.itemFromIndex(indextoremove)

        def documenttoremove(itemtoremove):
            self.showbuttons()

            data = itemtoremove.data(role=Qt.UserRole)
            self.willberemoved[data] = itemtoremove.background()
            itemtoremove.setBackground(QBrush(QColor("red")))
            itemtoremove.setData(False)
            self.documentstodelete.append(data)
            children = self.findallchildren(itemtoremove)
            if children:
                for child in children:
                    documenttoremove(child)


        def documenttonotremove(itemtonotremove):
            parentname = itemtonotremove.parent().data(Qt.UserRole)
            if parentname not in self.willberemoved:
                data = itemtonotremove.data(role=Qt.UserRole)
                oldbrush = self.willberemoved[data]
                del self.willberemoved[data]
                itemtonotremove.setBackground(QBrush(oldbrush))
                itemtonotremove.setData(True)
                self.documentstodelete.remove(data)
                children = self.findallchildren(itemtonotremove)
                if children:
                    for child in children:
                        documenttonotremove(child)
                self.removemessage.hide()
            else:
                self.removemessage.show()

        def rename(itemtorename):
            self.tree.edit(itemtorename.index())

        def addnewdocument(parentitem):
            newitem = QStandardItem()
            parentitem.appendRow(newitem)
            self.tree.edit(newitem.index())

        menu.popup(self.tree.mapToGlobal(pos))

    def createnew(self):
        for catitem in self.categoriestocreate:
            if not catitem:
                return
            prefix = catitem.text()
            if prefix in list(map(lambda x: x.prefix, self.db.root.documents)) or prefix == '':
                self.model.removeRow(catitem.row(), catitem.parent().index())
                self.categoriestocreate.remove(catitem)
                return
            for char in self.badcharacters:
                if char in prefix:
                    prefix.replace(char, '_')
            self.model.blockSignals(True)
            catitem.setData(prefix, role=Qt.UserRole)
            self.model.blockSignals(False)
            path = self.path + prefix
            parent = catitem.parent().text()
            print('{} {} {}'.format(prefix, parent, path), flush=True)
            self.db.root.create_document(path, prefix, parent=parent)

        self.categoriestocreate = []


    def buildlist(self):
        if self.db is None or len(self.db.root.documents) == 0:
            return
        self.model.clear()
        self.createhierarchy()
        self.tree.setCurrentIndex(self.model.index(0, 0))

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
        self.hidebuttons()

    def onrevert(self):
        self.db.reload()
        self.hidebuttons()

    def showbuttons(self):
        self.apply.show()
        self.revert.show()

    def hidebuttons(self):
        self.apply.hide()
        self.revert.hide()


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


    def deletependingdocuments(self):
        if len(self.documentstodelete) == 0:
            return
        for data in self.documentstodelete:
            self.docsdict[str(data)].delete()
            del self.docsdict[str(data)]
        self.documentstodelete = []

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
        self.showbuttons()

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

    def callback(self, func):
        def clb(selectionmodel):
            try:
                index = selectionmodel.indexes()[0]
                cat = index.data(Qt.UserRole)
            except IndexError:
                cat = None
            func(cat)
        self.tree.selectionModel().selectionChanged.connect(clb)

    def select(self, category=None):
        movedobject = self.tree.currentIndex()

        nextlist = self.getnext(movedobject, [])
        previouslist = self.getprevious(movedobject, [])
        currentobjects_list = previouslist + nextlist
        if category is None:
            currentindex = previouslist[0]
            self.tree.setCurrentIndex(currentindex)
            return
        for index in currentobjects_list:
            if index.data() == category:
                currentindex = index
                self.tree.setCurrentIndex(currentindex)



