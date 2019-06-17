from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .icon import Icon
from .categoryselector import CategorySelector
from markdown import markdown


class DocumentTreeView(QWidget):
    def __init__(self, parent=None):
        super(DocumentTreeView, self).__init__(parent)
        self.tree = QTreeView()
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.header().hide()
        self.tree.setIndentation(20)
        self.model = QStandardItemModel()

        self.category = None
        self.db = None
        self.editview = None
        self.icons = Icon()

        catselgrid = QHBoxLayout()
        catselgrid.setSpacing(10)
        catselgrid.setContentsMargins(0, 0, 0, 0)

        self.catselector = CategorySelector()
        self.catselector.callback(self.buildtree)

        self.newcatbtn = QPushButton(self.icons.FileDialogNewFolder, '')
        self.newcatbtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        catselgrid.addWidget(self.catselector)
        catselgrid.addWidget(self.newcatbtn)

        self.selectionclb = None
        oldSelectionChanged = self.tree.selectionChanged
        def selectionChanged(selected, deselected):
            if self.selectionclb is not None:
                self.selectionclb(self.selecteduid())

            oldSelectionChanged(selected, deselected)

        self.tree.selectionChanged = selectionChanged

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.contextmenu)
        self.tree.setModel(self.model)

        self.grid = QVBoxLayout()
        catsel = QWidget()
        catsel.setLayout(catselgrid)
        self.grid.addWidget(catsel)
        self.grid.addWidget(self.tree)
        self.setLayout(self.grid)

        self.lastselected = {}
        self.collapsed = set()
        self.tree.collapsed.connect(lambda x: self.collapsed.add(self.uidfromindex(x)))
        self.tree.expanded.connect(lambda x: self.collapsed.discard(self.uidfromindex(x)))

        self.uid_to_item = {}

        self.model.layoutChanged.connect(self.onlayoutchanged)

        copyshortcut = QShortcut(QKeySequence("Ctrl+C"), self.tree)
        def copy():
            if self.clipboard is None:
                return
            return self.clipboard(str(self.selecteduid()))

        copyshortcut.activated.connect(copy)


    def onlayoutchanged(self):
        movedobject = self.tree.currentIndex()
        nextlist = self.getnext(movedobject, [])
        previouslist = self.getprevious(movedobject, [])
        currentobjects_list = previouslist + nextlist

        topindices = []
        for index in currentobjects_list:
            if self.itemtouid(self.model.itemFromIndex(index).parent()) == None:
                topindices.append(index)

        treeofitems = []
        for i, top in enumerate(topindices):
            branch = self.treeofpointers(self.model.itemFromIndex(top), {}, self.model.itemFromIndex(movedobject))
            treeofitems.append(branch)
        '''
        #Prints tree in command line:
        tree = []
        for i, top in enumerate(topindices):
            branch = self.findplacepointers(self.model.itemFromIndex(top), {}, self.model.itemFromIndex(movedobject))
            tree.append(branch)
        for t in tree:
            self.printtree(t, 1)
        '''
        self.rename(treeofitems)

    def rename(self, tree):
        for i, t in enumerate(tree):
            self.namerecursively(t, str(i+1), 1)

    def namerecursively(self, t, level, sublevel):
        for keys, values in t.items():
            item = values[0]  # first value in the list of each key is the item of the key
            self.setlevelfromitem(item, level)
            self.updateuidfromitem(item)
            for i, value in enumerate(values[1:]):
                child_level = level+'.'+str(i+1)
                if type(value) == QStandardItem:
                    self.setlevelfromitem(value, child_level)
                    self.updateuidfromitem(value)
                elif type(value) == dict:
                    self.namerecursively(value, child_level, sublevel+1)


    def printtree(self, tree, level):
            for keys, values in tree.items():
                print('\t'*(level-1), keys, flush=True)
                for value in values:
                    if type(value) != dict:
                        print('\t'*level, value, flush=True)
                    elif type(value) == dict:
                        self.printtree(value, level+1)

    def itemtouid(self, item):
        return self.uidfromindex(self.model.indexFromItem(item))

    def treeofitems(self, item, dictofdicts, moved):
        if item.hasChildren():
            dictofdicts[self.itemtouid(item)] = []
            children = self.findallchildren(item)

            for child in children:
                if child is not moved:
                    if child.parent() == item:
                        dictofdicts[self.itemtouid(item)].append(self.treeofitems(child, {}, moved))

            return dictofdicts
        elif not item.hasChildren() and item.parent() is None:
            return {self.itemtouid(item): []}
        else:
            return self.itemtouid(item)

    def treeofpointers(self, item, dictofdicts, moved):
        if item.hasChildren():
            dictofdicts[self.itemtouid(item)] = [item]
            children = self.findallchildren(item)

            for child in children:
                if child is not moved:
                    if child.parent() == item:
                        dictofdicts[self.itemtouid(item)].append(self.treeofpointers(child, {}, moved))

            return dictofdicts
        elif not item.hasChildren() and item.parent() is None:
            return {self.itemtouid(item): [item]}
        else:
            return item

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



    def getnext(self, index, nextobjectslist):
        nextobject = self.tree.indexBelow(index)
        if self.uidfromindex(nextobject) != None:
            nextobjectslist.append(nextobject)
            self.getnext(nextobject, nextobjectslist)
        return nextobjectslist

    def getprevious(self, index, nextobjectslist):
        previousobject = self.tree.indexAbove(index)
        if self.uidfromindex(previousobject) != None:
            nextobjectslist.insert(0, previousobject)
            self.getprevious(previousobject, nextobjectslist)
        else:
            self.tree.setRootIndex(previousobject)
        return nextobjectslist


    def contextmenu(self, pos):
        menu = QMenu(parent=self.tree)
        si = self.tree.selectedIndexes()

        def createdocument(sibling=True):
            level = None
            lastsibling = None
            if len(si) > 0:
                if sibling:
                    parent = self.model.itemFromIndex(si[0]).parent()
                    if parent is not None:
                        data = self.model.data(self.model.indexFromItem(parent), Qt.UserRole)
                        level = str(data.level).split('.')
                        lastsibling = parent.child(parent.rowCount() - 1)
                else:
                    cur = self.model.itemFromIndex(si[0])
                    rows = cur.rowCount()
                    if rows == 0:
                        lastsibling = cur
                    else:
                        lastsibling = cur.child(rows - 1)
                    data = self.model.data(si[0], Qt.UserRole)
                    level = str(data.level)

            if lastsibling is None:
                rows = self.model.rowCount()
                lastsibling = self.model.itemFromIndex(self.model.index(rows - 1, 0))
                level = ['1']

            data = self.model.data(self.model.indexFromItem(lastsibling), Qt.UserRole)
            if data is not None:
                level = str(data.level).split('.')[:len(level)]
                level[-1] = str(int(level[-1]) + 1)
            if len(level) < 2:
                level.append('0')
            level = '.'.join(level)
            item = self.db.root.add_item(self.category, level=level)
            self.db.reload()

        if len(si) > 0:
            data = self.model.data(si[0], Qt.UserRole)
            act = menu.addAction(self.icons.FileIcon, 'Create sibling document')
            act.triggered.connect(lambda: createdocument())
            act = menu.addAction(self.icons.FileIcon, 'Create child document')
            act.triggered.connect(lambda: createdocument(False))
            if str(data.level).split('.')[-1] != '0':
                act.setEnabled(False)

            menu.addSeparator()
            act = menu.addAction('Remove document')
            def removedocument(uid):
                self.db.remove(uid)
            act.triggered.connect(lambda: removedocument(data.uid))
        else:
            act = menu.addAction(self.icons.FileIcon, 'Create document')
            act.triggered.connect(lambda: createdocument())
        menu.addSeparator()
        menu.addAction('Expand all').triggered.connect(lambda: self.tree.expandAll())
        def collapse():
            self.tree.collapseAll()
            self.tree.clearSelection()
        menu.addAction('Collapse all').triggered.connect(collapse)
        menu.popup(self.tree.mapToGlobal(pos))

    def buildtree(self, cat=None):
        self.lastselected[str(self.category)] = self.selecteduid()
        self.model.clear()
        if self.db is None or len(self.db.root.documents) == 0:
            return
        if cat is None:
            if self.category is not None:
                cat = self.category
            else:
                cat = self.db.root.documents[0].prefix
        self.category = cat
        c = [x for x in self.db.root if x.prefix == cat][0]
        items = {}
        for doc in sorted(c, key=lambda x: x.level):
            level = str(doc.level)
            level = level.split('.')
            if level[-1] == '0':
                level = level[:-1]
            level = '.'.join(level)
            uid = str(doc.uid)
            item = QStandardItem()
            self.uid_to_item[str(doc.uid)] = [item, doc]
            item.setData(doc, role=Qt.UserRole)
            items[level] = item
            up = level.split('.')[:-1]
            up = '.'.join(up)
            if up != level and up in items:
                items[up].appendRow(item)
            else:
                self.model.appendRow(item)
            index = self.model.indexFromItem(item)
            if str(doc.uid) not in self.collapsed:
                self.tree.expand(index)
            if str(cat) in self.lastselected and str(doc.uid) == self.lastselected[str(cat)]:
                self.tree.setCurrentIndex(index)
            self.updateuid(uid)
        if len(self.tree.selectedIndexes()) == 0:
            self.tree.setCurrentIndex(self.model.index(0, 0))

    def connectdb(self, db):
        self.db = db
        self.buildtree()
        self.catselector.connectdb(db)


    def connectview(self, view):
        self.editview = view

    def connectcreatecatdiag(self, createcatdiag):
        self.createcatdiag = createcatdiag
        self.newcatbtn.clicked.connect(self.createcatdiag.show)

    def uidfromindex(self, index):
        data = self.model.data(index, role=Qt.UserRole)
        if data is not None:
            return str(data.uid)
        return None

    def levelfromindex(self, index):
        data = self.model.data(index, role=Qt.UserRole)
        if data is not None:
            return str(data.level)
        return None

    def setlevelfromitem(self, item, level):
        index = self.model.indexFromItem(item)
        data = self.model.data(index, role=Qt.UserRole)
        if data is not None:
            data.level = level
        return None


    def selecteduid(self):
        selected = self.tree.selectedIndexes()
        if len(selected) > 0:
            return self.uidfromindex(selected[0])
        return None

    def updateuid(self, uid):
        if uid not in self.uid_to_item:
            return
        item = self.uid_to_item[uid][0]
        data = self.uid_to_item[uid][1]
        level = str(data.level)
        if data.heading:
            heading = data.text
            heading = markdown(heading.split('\n')[0])
            text = QTextDocument()
            text.setHtml(heading)
            title = '{} {}'.format(level, text.toPlainText())
        else:
            title = '{} {}'.format(level, uid)
        item.setText(title)

    def updateuidfromitem(self, item):
        index = self.model.indexFromItem(item)
        data = self.model.data(index, role=Qt.UserRole)
        level = str(data.level)
        if data.heading:
            heading = data.text
            heading = markdown(heading.split('\n')[0])

            text = QTextDocument()
            text.setHtml(heading)
            title = '{} {}'.format(level, text.toPlainText())
        else:
            start = '**Feature name:**'
            end = "**Feature requirement:**"
            dt = data.text
            if start in dt and end in dt:
                text = dt[dt.find(start) + len(start):dt.rfind(end)].strip()
            elif start in dt and end not in dt:
                text = dt[dt.find(start) + len(start):].strip()
            else:
                uid = self.uidfromindex(index)
                text = uid
            title = '{} {}'.format(level, text)
        item.setText(title)

    def read(self, uid):
        if self.db is None:
            return
        item = self.db.find(uid)
        cat = str(item.parent_documents[0])
        self.lastselected[cat] = str(uid)
        self.catselector.select(cat)


