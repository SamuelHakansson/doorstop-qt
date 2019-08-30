from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .customcompleter import CustomQCompleter
import os
from pathlib import Path
from .revertbutton import RevertButton
from .icon import Icon
from .searchlayout import SearchLayout
import shutil
from .nameregex import Nameregex
import string


class DocumentView(QWidget):
    def __init__(self, parent=None, header='', iconcolor=None):
        super(DocumentView, self).__init__(parent)

        self.vbox = QVBoxLayout()
        grid = QVBoxLayout()
        self.model = QStandardItemModel()

        self.tree = QTreeView()
        self.tree.header().hide()
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.setIndentation(20)

        grid.addWidget(self.tree)

        self.warningmessage = QLabel('Warning: only one root allowed. \n          Layout is not saved')
        self.warningmessage.setStyleSheet('color: red')
        self.warningmessage.hide()

        papirusicons = Icon(iconcolor)
        foldericon = papirusicons.fromTheme("folder-open")

        self.revert = RevertButton()

        self.db = None

        self.searchlayout = SearchLayout('Search item')
        self.completer = CustomQCompleter()
        self.searchlayout.searchbox.setCompleter(self.completer)
        self.header = QLabel(header)
        font = QFont()
        font.setBold(True)
        self.header.setFont(font)
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.header)
        self.folderbutton = QPushButton(foldericon, '')
        self.hbox.addStretch(1)
        self.hbox.addWidget(self.folderbutton)
        self.vbox.addLayout(self.hbox)
        self.vbox.addLayout(self.searchlayout)
        self.vbox.addWidget(self.tree)
        self.setLayout(self.vbox)

        self.tree.setModel(self.model)

        self.model.layoutChanged.connect(self.onlayoutchanged)

        self.revert.setParent(self.tree)
        self.warningmessage.setParent(self.tree)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.contextmenu)

        self.model.itemChanged.connect(self.namechanged)
        self.documentstodelete = []
        self.namechangeditems = []
        self.doctonewname = {}
        self.willberemoved = {}
        self.documentstocreate = []
        self.gotoclb = None
        self.completer.activated.connect(self.gotocompleted)

        self.treestack = []
        self.revert.clicked.connect(self.undowrap)
        self.docsdict = {}
        self.LEVELS = 0
        self.REMOVE = 1
        self.NEW = 2
        self.currentdocument = None
        self.reloaddatabase = None
        self.folderbutton.clicked.connect(self.selectfolder)
        self.reloaditemfunc = None
        self.nameregex = Nameregex()
        self.completerdict = {}
        self.icons = [foldericon]

    def selectfolder(self):
        if self.reloaddatabase:
            self.reloaddatabase()

    def updateCompleter(self):
        docs = list(map(lambda x: x, self.db.root.documents))
        texts = []
        self.completerdict = {}
        for doc in docs:
            for item in doc.items:
                dt = item.text
                uid = str(item.uid)
                text = self.nameregex.gettitle(dt)
                if text:
                    text = uid + ' | ' + text
                else:
                    text = uid
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
        if searchstr not in self.completerdict:
            return
        uid = self.completerdict[searchstr]
        self.goto(uid)

    def namechanged(self, changeditem):
        self.namechangeditems.append(changeditem)
        self.setnewnames()

    def setnewnames(self): #  uses a list to be able to use an apply button
        for changeditem in self.namechangeditems:
            doc = changeditem.data(Qt.UserRole)
            newname = changeditem.text()
            if doc:
                if doc != newname:
                    newname = self.formatname(newname)
                    self.doctonewname[str(doc)] = newname
                    changeditem.setText(newname)

                    changeddoc = self.docsdict[str(doc)]
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
                self.documentstocreate.append(changeditem)

        self.namechangeditems = []
        self.createnew()

    def show(self):
        super(DocumentView, self).show()

    def connectdb(self, db):
        self.db = db
        self.docs = [x for x in self.db.root]
        for d in self.docs:
            self.docsdict[str(d)] = d
        #self.model.blockSignals(True)
        self.buildlist()
        self.select(self.currentdocument)
        #self.model.blockSignals(False)
        self.updateCompleter()
        self.moverevertbutton()

    def contextmenu(self, pos):
        menu = QMenu(parent=self.tree)
        si = self.tree.selectedIndexes()
        if len(si) > 0:
            selectedindex = si[0]
            item = self.model.itemFromIndex(selectedindex)

            addaction = menu.addAction("Create child document")
            addaction.triggered.connect(lambda: addnewdocument(item))
            addsiblingaction = menu.addAction("Create sibling document")
            if item.parent() is None:
                addsiblingaction.setDisabled(True)
            addsiblingaction.triggered.connect(lambda: addnewdocument(item, child=False))
            menu.addSeparator()
            renameaction = menu.addAction("Rename")
            renameaction.triggered.connect(lambda: rename(item))
            menu.addSeparator()

            removeaction = menu.addAction('Remove')
            removeaction.triggered.connect(lambda: remove(item))
        else:
            addaction = menu.addAction("Create document")
            addaction.triggered.connect(lambda: addnewdocument())

        def remove(item):
            documenttoremove(item)
            removeandreload()

        def documenttoremove(itemtoremove):
            data = itemtoremove.data(role=Qt.UserRole)
            self.documentstodelete.append(data)
            children = self.findallchildren(itemtoremove)
            if children:
                for child in children:
                    documenttoremove(child)

            doc = self.docsdict[str(data)]
            docpath = Path(doc.path)
            listdir = os.listdir(doc.path)
            itemsindoc = [Path(docpath)]
            for file in listdir:
                path = Path(doc.path)
                filepath = path / file
                backupfile = open(filepath, 'rb').read()
                itemsindoc.append((backupfile, filepath))
            self.treestack.append((itemsindoc, self.REMOVE))

        def removeandreload():

            for data in self.documentstodelete:
                doc = self.docsdict[str(data)]
                if os.path.isdir(Path(doc.path)):
                    shutil.rmtree((Path(doc.path)))
                    del self.docsdict[str(data)]
            self.documentstodelete = []
            self.moverevertbutton()
            self.revert.show()
            self.db.reload()

        def rename(itemtorename):
            self.tree.edit(itemtorename.index())

        def addnewdocument(parentitem=None, child=True):
            newitem = QStandardItem()
            if parentitem:
                if child:
                    parentitem.appendRow(newitem)
                else:
                    parentitem.parent().appendRow(newitem)
            else:
                self.model.appendRow(newitem)
            if newitem.parent():
                self.tree.expand(newitem.parent().index())
            self.tree.edit(newitem.index())

        menu.popup(self.tree.mapToGlobal(pos))

    def format_filename(self, s):
        """Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores.

    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename.

    """
        valid_chars = "-_ %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in s if c in valid_chars)
        filename = filename.replace(' ', '_')  # I don't like spaces in filenames.
        return filename

    def removeunwantedrowanddoc(self, docitem):
        if docitem.parent():
            self.model.removeRow(docitem.row(), docitem.parent().index())
        else:
            self.model.removeRow(docitem.row())
        self.documentstocreate.remove(docitem)

    def formatname(self, name):
        if not name:
            return
        prefix = name
        prefix = self.format_filename(prefix)
        if not prefix or prefix == '':
            return

        if prefix[-1].isnumeric():
            prefix = prefix + '_'

        while prefix[0] == "-" or prefix[0] == '_' or prefix[0].isdigit():
            prefix = prefix[1:]
            if len(prefix) == 0:
                break

        return prefix

    def createnew(self):
        for docitem in self.documentstocreate:
            if not docitem:
                return
            prefix = self.formatname(docitem.text())

            if prefix in list(map(lambda x: x.prefix, self.db.root.documents)) or prefix == '' or prefix is None or \
                    not (any(char.isdigit() or char.isalpha() for char in prefix)):
                self.removeunwantedrowanddoc(docitem)
                return

            self.model.blockSignals(True)
            docitem.setText(prefix)
            docitem.setData(prefix, role=Qt.UserRole)
            self.model.blockSignals(False)
            path = Path(self.db.root.root, prefix)
            if docitem.parent():
                parent = docitem.parent().text()
            else:
                parent = None
            print('{} {} {}'.format(prefix, parent, path), flush=True)
            doc = self.db.root.create_document(path, prefix, parent=parent)
            self.docsdict[prefix] = doc
            self.tree.setCurrentIndex(docitem.index())
            self.treestack.append((doc, self.NEW))
            self.currentdocument = doc
            self.moverevertbutton()
            self.revert.show()
        self.documentstocreate = []

    def buildlist(self):
        self.model.clear()
        if self.db is None or len(self.db.root.documents) == 0:
            if self.reloaditemfunc:
                self.reloaditemfunc(None)
            return
        self.model.blockSignals(True)
        self.createhierarchy()
        self.model.blockSignals(False)

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
        self.select(self.currentdocument)

    def undowrap(self):
        self.undo()
        self.undoreload()

    def undo(self):

        stack = self.treestack[-1][0]
        type = self.treestack[-1][1]
        if type == self.LEVELS:
            for obj in stack:
                document, documentparent = obj
                if document.parent != documentparent:
                    if documentparent:
                        document.parent = documentparent
                    else:
                        document._data['parent'] = None
                        document.save()

                nrroots = 0
                for obj in self.docs:
                    pardata = obj.parent
                    if pardata is None:
                        nrroots += 1
                if nrroots != 1:
                    del self.treestack[-1]
                    self.undo()
                else:
                    self.warningmessage.hide()
                    self.moverevertbutton()

        elif type == self.REMOVE:
            folder = stack[0]
            if not os.path.exists(folder):
                os.mkdir(folder)
            for oldfile in stack[1:]:
                data, path = oldfile
                file = open(path, "wb+")
                file.write(data)
                file.close()

        elif type == self.NEW:
            doc = stack
            doc.delete()

    def undoreload(self):
        self.db.reload()
        self.reloadtree()
        self.buildlist()
        del self.treestack[-1]
        if not self.treestack:
            self.revert.hide()

    def reloadtree(self):
        docs = self.db.root.documents
        root = self.db.root.root
        newtree = self.db.root.from_list(docs, root)
        self.db.root = newtree

    def changehierarchy(self, currentobjects_list):
        for obj in currentobjects_list:
            temp = []
            data = self.model.data(obj, role=Qt.UserRole)
            parindex = obj.parent()

            pardata = self.model.data(parindex, role=Qt.UserRole)
            document = self.docsdict[data]
            if document.parent != pardata:
                temp.append((document, document.parent))
                self.treestack.append((temp, self.LEVELS))
                if pardata is not None:
                    document.parent = pardata
                else:
                    document._data['parent'] = None
                    document.save()

    def onlayoutchanged(self):
        rootobject = self.model.index(0, 0)
        currentindex = self.tree.currentIndex()
        moveddata = currentindex.data(role=Qt.UserRole)

        nextlist = self.getnextlist(rootobject, [])

        for i, index in enumerate(nextlist):
            if index.data(role=Qt.UserRole) == moveddata and index == currentindex:
                del nextlist[i]
                break

        currentobjects_list = [rootobject] + nextlist

        nrroots = 0
        for obj in currentobjects_list:
            parindex = obj.parent()
            pardata = self.model.data(parindex, role=Qt.UserRole)
            if pardata is None:
                nrroots += 1
        if nrroots != 1:
            self.warningmessage.show()
            self.moverevertbutton()

        else:
            self.warningmessage.hide()
            self.changehierarchy(currentobjects_list)
            self.revert.show()
        self.tree.expandAll()

    def getnextlist(self, index, nextobjectslist):
        nextobject = self.tree.indexBelow(index)
        data = self.model.data(nextobject, role=Qt.UserRole)
        if data is not None:
            nextobjectslist.append(nextobject)
            self.getnextlist(nextobject, nextobjectslist)
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
                doc = index.data(Qt.UserRole)
                self.currentdocument = doc
            except IndexError:
                doc = None
            func(doc)
        self.reloaditemfunc = func
        self.tree.selectionModel().selectionChanged.connect(clb)

    def select(self, document=None):
        movedobject = self.model.index(0, 0)
        nextlist = self.getnextlist(movedobject, [])
        currentobjects_list = [movedobject] + nextlist
        if document is None:
            currentindex = self.model.index(0, 0)
            self.tree.setCurrentIndex(currentindex)
            return
        for index in currentobjects_list:
            if index.data() == str(document):
                self.tree.setCurrentIndex(index)
                return

    def moverevertbutton(self):
        self.revert.move(self.tree.width() - 43, self.tree.height() - 35)
        warnwidth = self.warningmessage.width()
        self.warningmessage.move(int((self.tree.width() - warnwidth)/2), self.tree.height() - 30)

    def read(self, uid):
        if self.db is None:
            return
        item = self.db.find(uid)
        doc = str(item.parent_documents[0])
        self.select(doc)


