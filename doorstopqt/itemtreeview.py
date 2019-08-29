from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .icon import Icon
from .requirement_template import newitemtext
from .customtree import CustomTree
from .revertbutton import RevertButton
import pathlib
from .nameregex import Nameregex


class ItemTreeView(QWidget):
    def __init__(self, parent=None, attributeview=None):
        super(ItemTreeView, self).__init__(parent)

        self.tree = CustomTree()

        self.model = QStandardItemModel()
        self.attributeview = attributeview

        self.document = None
        self.db = None
        self.editview = None
        self.icons = Icon()
        self.lastdocument = None

        self.revertbtn = RevertButton()

        self.setlinkfunc = None
        self.selectionclb = None
        oldSelectionChanged = self.tree.selectionChanged

        def selectionChanged(selected, deselected):
            if self.selectionclb is not None:
                self.selectionclb(self.selecteduid())
                if self.document == self.lastdocument:
                    currentuid = self.tree.currentIndex().data(Qt.UserRole)
                    if self.setlinkfunc:
                        linkuid = self.setlinkfunc(currentuid)
                        if linkuid:
                            uid = self.db.find(linkuid)
                            self.docview.select(str(uid.document))
                            item = self.uidtoitem(linkuid)
                            self.tree.setCurrentIndex(self.model.indexFromItem(item))
                self.lastdocument = self.document
            oldSelectionChanged(selected, deselected)

        self.tree.selectionChanged = selectionChanged

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.contextmenu)
        self.tree.setModel(self.model)

        self.grid = QVBoxLayout()
        self.hbox = QHBoxLayout()
        self.revertbtn.setParent(self.tree)

        self.grid.addWidget(self.tree)
        self.setLayout(self.grid)

        self.lastselected = {}
        self.collapsed = set()
        self.tree.collapsed.connect(lambda x: self.collapsed.add(self.uidfromindex(x)))
        self.tree.expanded.connect(lambda x: self.collapsed.discard(self.uidfromindex(x)))

        self.uid_to_item = {}
        self.uid_to_checkboxes = {}

        self.model.layoutChanged.connect(self.layoutwrapper)

        self.layoutchange_cooldown = 0

        self.newitemtext = newitemtext
        self.fullstack = {}
        self.treestack = []
        self.LEVELS = 0
        self.REMOVE = 1
        self.NEW = 2

        self.headerlabel = ['Requirement', 'Active', 'Derived', 'Normative', 'Heading']

        self.otherdbviews = []
        self.currentuid = None
        self.regexer = Nameregex()

        copyshortcut = QShortcut(QKeySequence("Ctrl+C"), self.tree)

        def copy():
            if self.clipboard is None:
                return
            return self.clipboard(str(self.selecteduid()))

        copyshortcut.activated.connect(copy)
        self.revertbtn.clicked.connect(self.undo)

    def active_link(self, s):
        self.setcheckboxvalue(s=s, attribute=1)

    def derived_link(self, s):
        self.setcheckboxvalue(s=s, attribute=2)

    def normative_link(self, s):
        self.setcheckboxvalue(s=s, attribute=3)

    def heading_link(self, s):
        self.setcheckboxvalue(s=s, attribute=4)

    def setcheckboxvalue(self, s, attribute):
        uid = self.attributeview.currentuid
        self.setcheckboxfromuid(s, uid, attribute)

    def uidtoguiindex(self, uid):
        if uid is None:
            return
        treeindices = self.gettreeindices()
        for index in treeindices:
            if index.data(Qt.UserRole) == str(uid):
                return index

    def uidtoitem(self, uid):
        if uid is None:
            return
        data = self.db.find(uid)
        leveltuple = data.level.value
        leveldecrease = 0
        if leveltuple[-1] == 0:
            leveldecrease = 1
        levelsteps = len(leveltuple) - leveldecrease
        item = self.model.item(leveltuple[0]-1, 0)
        for l in range(0, levelsteps-1):
            l += 1
            try:
                item = item.child(leveltuple[l]-1, 0)
            except AttributeError:
                return
        return item

    def uidtoindex(self, uid):
        treeaslist = self.gettreeaslist()
        for index in treeaslist:
            if str(index.data(Qt.UserRole)) == str(uid):
                return index

    def setcheckboxfromuid(self, state, uid, attribute):
        if uid is None:
            return

        data = self.db.find(uid)
        leveltuple = data.level.value
        leveldecrease = 0
        if leveltuple[-1] == 0:
            leveldecrease = 1
        levelsteps = len(leveltuple) - leveldecrease
        whichobject = [0]*levelsteps
        whichobject[-1] = attribute
        if levelsteps-1 == 0:
            col = attribute
        else:
            col = 0
        item = self.model.item(leveltuple[0]-1, col)
        for l in range(0, levelsteps-1):
            l += 1
            item = item.child(leveltuple[l]-1, whichobject[l])
        if item is not None:
            item.setCheckState(state)

    def layoutwrapper(self):
        # if this is not used, layoutChange will be called five times, one for every column
        if self.layoutchange_cooldown == 4:
            self.onlayoutchanged()
        self.layoutchange_cooldown += 1
        self.layoutchange_cooldown %= 5

    def gettreeindices(self):
        movedobject = self.model.index(0, 0)
        nextlist = self.getnext(movedobject, [])
        currentobjects_list = nextlist
        return currentobjects_list

    def gettreeaslist(self):
        movedobject = self.tree.currentIndex()

        movedobject = movedobject.siblingAtColumn(0)
        nextlist = self.getnext(movedobject, [])
        previouslist = self.getprevious(movedobject, [])
        currentobjects_list = previouslist + [movedobject] + nextlist
        return currentobjects_list

    def onlayoutchanged(self):
        movedobject = self.tree.currentIndex()
        movedobject = movedobject.siblingAtColumn(0)
        nextlist = self.getnext(movedobject, [])
        previouslist = self.getprevious(movedobject, [])
        currentobjects_list = previouslist + nextlist

        self.savelevels()
        currentobjects_list = self.gettreeaslist()
        topindices = []
        for index in currentobjects_list:
            if self.itemtouid(self.model.itemFromIndex(index).parent()) is None:
                topindices.append(index)

        treeofitems = []
        for i, top in enumerate(topindices):
            branch = self.treeofpointers(self.model.itemFromIndex(top), {}, self.model.itemFromIndex(movedobject))
            treeofitems.append(branch)

        self.rename(treeofitems)
        self.setupHeaders()

    def rename(self, tree):
        for i, t in enumerate(tree):
            self.namerecursively(t, str(i+1), 1)

    def namerecursively(self, t, level, sublevel):
        for keys, values in t.items():
            item = values[0]  # first value in the list of each key is the item of the key
            self.setlevelfromitem(item, level)
            self.updateuidfromitem(item)
            self.tree.expand(item.index())
            for i, value in enumerate(values[1:]):
                child_level = level+'.'+str(i+1)
                if type(value) == QStandardItem:

                    self.setlevelfromitem(value, child_level)
                    self.updateuidfromitem(value)
                elif type(value) == dict:
                    self.namerecursively(value, child_level, sublevel+1)

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

    def getnext(self, index, nextindexlist):
        nextindex = self.tree.indexBelow(index)
        if self.uidfromindex(nextindex) is not None:
            nextindexlist.append(nextindex)
            self.getnext(nextindex, nextindexlist)
        return nextindexlist

    def getprevious(self, index, nextobjectslist):
        previousobject = self.tree.indexAbove(index)
        if self.uidfromindex(previousobject) is not None:
            nextobjectslist.insert(0, previousobject)
            self.getprevious(previousobject, nextobjectslist)
        else:
            self.tree.setRootIndex(previousobject)
        return nextobjectslist

    def contextmenu(self, pos):
        menu = QMenu(parent=self.tree)
        si = self.tree.selectedIndexes()

        def createrequirement(sibling=True):
            level = None
            lastsibling = None
            nochildren = False
            if len(si) > 0:
                cur = self.model.itemFromIndex(si[0])
                if sibling:
                    parent = cur.parent()
                    if parent is not None:
                        data = self.model.data(self.model.indexFromItem(parent), Qt.UserRole)
                        level = str(data.level).split('.')
                        lastsibling = parent.child(parent.rowCount() - 1)
                else:
                    rows = cur.rowCount()
                    if rows == 0:
                        lastsibling = cur
                        nochildren = True
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
                level = str(data.level).split('.')#[:len(level)]
                if data.heading:
                    del level[-1]
                if not nochildren:
                    level[-1] = str(int(level[-1]) + 1)
                else:
                    level.append('1')

            level = '.'.join(level)
            item = self.db.root.add_item(self.document, level=level, reorder=False)
            item.text = self.newitemtext
            self.db.reload()
            itemtoselect = self.uidtoitem(item.uid)
            if itemtoselect:
                self.tree.setCurrentIndex(itemtoselect.index())
            self.treestack.append((item.uid, self.NEW))
            self.revertbtn.show()

        if len(si) > 0:
            data = self.model.data(si[0], Qt.UserRole)
            act = menu.addAction(self.icons.FileIcon, 'Create sibling item')
            act.triggered.connect(lambda: createrequirement())
            act = menu.addAction(self.icons.FileIcon, 'Create child item')
            act.triggered.connect(lambda: createrequirement(False))

            menu.addSeparator()
            act = menu.addAction('Remove item')

            def removerequirement(item):
                backupfile = open(item.path, 'rb').read()
                self.treestack.append(((backupfile, item.path), self.REMOVE))
                uid = item.uid
                data = item.data
                for otherdbview in self.otherdbviews:
                    if otherdbview.key in data:
                        linkeduids = data[otherdbview.key]
                        for linkeduid in linkeduids:
                            otheritem = otherdbview.otherdb.find(linkeduid)
                            otherdbview.removeotherlink(otheritem, uid)
                self.db.remove(uid)
                self.db.reload()
                self.revertbtn.show()

            act.triggered.connect(lambda: removerequirement(data))
        else:
            act = menu.addAction(self.icons.FileIcon, 'Create item')
            act.triggered.connect(lambda: createrequirement())
            if len(self.db.root.documents) == 0:
                act.setDisabled(True)
        menu.addSeparator()
        menu.addAction('Expand all').triggered.connect(lambda: self.tree.expandAll())

        def collapse():
            self.tree.collapseAll()
            self.tree.clearSelection()
        menu.addAction('Collapse all').triggered.connect(collapse)
        menu.popup(self.tree.mapToGlobal(pos))

    def savelevels(self):

        self.revertbtn.show()
        stack = {}
        c = [x for x in self.db.root if x.prefix == self.document][0]

        for doc in sorted(c, key=lambda x: x.level):
            stack[doc] = str(doc.level)
        self.treestack.append((stack, self.LEVELS))

    def undo(self):
        if not self.treestack:
            self.revertbtn.hide()
            return

        stack = self.treestack[-1][0]
        type = self.treestack[-1][1]
        if type == self.LEVELS:
            c = [x for x in self.db.root if x.prefix == self.document][0]

            for doc in sorted(c, key=lambda x: x.level):
                doc.level = stack[doc]
            self.buildtree(self.document)

        elif type == self.REMOVE:
            data, path = stack
            file = open(path, "wb+")
            file.write(data)
            file.close()
            self.db.reload()
            uid = pathlib.Path(path).stem
            item = self.db.find(uid)
            for otherdbview in self.otherdbviews:
                if otherdbview.key in item.data:
                    for linkeduid in item.data[otherdbview.key]:
                        otherdbview.linkitems(uid, linkeduid)

        elif type == self.NEW:
            uid = stack
            self.db.remove(uid)

        del self.treestack[-1]
        if not self.treestack:
            self.revertbtn.hide()

    def loadstack(self, document):
        if document:
            if str(document) in self.fullstack:
                self.treestack = self.fullstack[str(document)]
            else:
                self.treestack = []

    def savestack(self, document):
        if document:
            self.fullstack[str(self.document)] = self.treestack

    def buildtree(self, doc=None):
        self.savestack(self.document)
        self.lastselected[str(self.document)] = self.selecteduid()
        self.model.clear()
        if self.db is None or len(self.db.root.documents) == 0:
            return
        if doc is None:
            if self.document is not None and self.document in list(map(lambda x: x.prefix, self.db.root.documents)):
                doc = self.document
            else:
                doc = self.db.root.documents[0].prefix
        self.document = doc
        self.loadstack(self.document)
        if self.treestack:
            self.revertbtn.show()
        else:
            self.revertbtn.hide()
        c = [x for x in self.db.root if x.prefix == doc][0]

        items = {}
        for doc in sorted(c, key=lambda x: x.level):
            level = str(doc.level)
            level = level.split('.')
            if level[-1] == '0':
                level = level[:-1]
            level = '.'.join(level)
            uid = str(doc.uid)
            item = QStandardItem()
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.uid_to_item[str(doc.uid)] = [item, doc]
            item.setData(doc, role=Qt.UserRole)
            items[level] = item
            up = level.split('.')[:-1]
            up = '.'.join(up)

            row = self.init_checkboxes(uid)
            row.insert(0, item)

            if up != level and up in items:
                items[up].appendRow(row)
            else:
                self.model.appendRow(row)
            index = self.model.indexFromItem(item)
            if str(doc.uid) not in self.collapsed:
                self.tree.expand(index)
            if str(doc.document) in self.lastselected and str(doc.uid) == self.lastselected[str(doc.document)]:
                self.tree.setCurrentIndex(index)
            self.updateuid(uid)
        if len(self.tree.selectedIndexes()) == 0:
            self.tree.setCurrentIndex(self.model.index(0, 0))

    def init_checkboxes(self, uid):
        activecheckbox = QStandardItem()
        derivedcheckbox = QStandardItem()
        normativecheckbox = QStandardItem()
        headingcheckbox = QStandardItem()

        checkboxrow = [activecheckbox, derivedcheckbox, normativecheckbox, headingcheckbox]
        self.uid_to_checkboxes[uid] = checkboxrow
        data = self.db.find(uid)
        checkboxattributes = [data.active, data.derived, data.normative, data.heading]
        checkboxnames = ['active', 'derived', 'normative', 'heading']
        for i, checkbox in enumerate(checkboxrow):
            checkbox.setData(checkboxnames[i])
            checkbox.setData(data, role=Qt.UserRole)
            checkbox.setCheckState(Qt.Checked if checkboxattributes[i] else Qt.Unchecked)
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        return checkboxrow

    def connectdb(self, db):
        self.db = db

    def updatecheckbox(self, s):
        checkboxinfo = s.data()
        if checkboxinfo is None:
            return
        data = s.data(role=Qt.UserRole)
        uid = data.uid
        data = self.db.find(uid)
        checkboxtype = s.data()

        item = self.uidtoitem(uid)
        if item:
            if checkboxtype == 'active':
                data.active = True if s.checkState() == Qt.Checked else False

            elif checkboxtype == 'derived':
                data.derived = True if s.checkState() == Qt.Checked else False

            elif checkboxtype == 'normative':
                if s.checkState() == Qt.Checked:
                    data.normative = True

                    if data.level.value[-1] == 0:
                        data.level = data.level.value[:-1]
                else:
                    data.normative = False

                self.setcheckboxfromuid(Qt.Checked if data.heading else Qt.Unchecked, uid, attribute=4)

                self.updateuidfromitem(item)
            elif checkboxtype == 'heading':

                if s.checkState() == Qt.Checked:
                    data.heading = True
                else:
                    data.heading = False

                self.setcheckboxfromuid(Qt.Checked if data.normative else Qt.Unchecked, uid, attribute=3)
                self.updateuidfromitem(item)

    def setupHeaders(self):
        self.model.setHorizontalHeaderLabels(self.headerlabel)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.setupHeaderwidth()

    def setheaderlabel(self, label):
        self.headerlabel[0] = label

    def setupHeaderwidth(self):
        self.tree.setColumnWidth(0, self.tree.width()-245)
        self.setposrevertbtn()

    def setposrevertbtn(self):

        #extrawidth = self.tree.verticalScrollBar().width()
        extraheight = self.tree.horizontalScrollBar().height()
        self.revertbtn.move(self.tree.width() - 50, self.tree.height() - extraheight - 30)

    def post_init(self):
        self.model.itemChanged.connect(self.updatecheckbox)

    def connectview(self, view):
        self.editview = view

    def connectdocview(self, docview):
        self.docview = docview
        self.docview.callback(self.buildtree)

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
            if data.heading is True:
                level += '.0'
            if str(data.level) == level:
                return
            uid = self.uidfromindex(index)
            dbitem = self.db.find(uid)
            data.level = level
            dbitem.level = level
            return True

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

        dt = data.text
        text = self.regexer.gettitle(dt)
        if text:
            text = '| ' + text
        else:
            text = ''
        title = '{} {} {}'.format(level, uid, text)
        item.setText(title)

    def updateuidfromitem(self, item):
        index = self.model.indexFromItem(item)
        data = self.model.data(index, role=Qt.UserRole)
        level = str(data.level)
        uid = self.uidfromindex(index)

        dt = data.text
        text = self.regexer.gettitle(dt)

        if text:
            text = '| '+text
        else:
            text = ''
        title = '{} {} {}'.format(level, uid, text)
        item.setText(title)

    def read(self, uid):
        if self.db is None:
            return
        if uid is None:
            return
        item = self.db.find(uid)
        cat = str(item.document)
        self.lastselected[cat] = str(uid)
        guiindex = self.uidtoindex(uid)
        if guiindex:
            self.tree.setCurrentIndex(guiindex)
        self.setupHeaders()

