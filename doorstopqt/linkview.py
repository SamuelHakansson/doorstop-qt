from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .linkitemmodel import LinkItemModel
from .icon import Icon
from .customcompleter import CustomQCompleter


class LinkView(QWidget):
    def __init__(self, markdownview, attribview, parent=None):
        super(LinkView, self).__init__(parent)

        self.vbox = QVBoxLayout()
        self.listview = QListView()
        self.icons = Icon()
        self.db = None
        self.model = LinkItemModel()
        self.listview.setModel(self.model)
        self.listview.setAlternatingRowColors(True)
        self.currentitemedit = None
        self.currentindexedit = None
        self.markdownview = markdownview
        self.attribview = attribview
        self.attribview.readlinkview = self.read

        self.completer = CustomQCompleter()
        self.completer.activated.connect(self.createlinkingitem)
        self.linkentry = QLineEdit()
        self.linkentry.setCompleter(self.completer)
        self.linkentry.setPlaceholderText('<Click here to add parent link>')
        self.vbox.addWidget(self.linkentry)
        self.vbox.addWidget(self.listview)
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbox)
        self.completerdict = {}


        def dataChanged(index):
            if self.db is None:
                return
            if self.currentuid is None:
                return

            item = self.model.itemFromIndex(index)
            uid = item.text()
            doc = self.db.find(uid)
            if doc is not None:
                self.db.root.link_items(self.currentuid, uid)

            self.goto(self.currentuid)
        self.model.dataChanged.connect(dataChanged)

        def clicked(index):
            item = self.model.itemFromIndex(index)
            if item.isEditable():
                self.currentitemedit = item
                self.currentindexedit = index
                self.edit(index)

        self.listview.clicked.connect(clicked)

        def dblclicked(index):
            item = self.model.itemFromIndex(index)
            data = item.data()
            if data is None or item.isEditable():
                return
            uid = data[1]
            self.goto(uid)
        self.listview.doubleClicked.connect(dblclicked)

        self.listview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listview.customContextMenuRequested.connect(self.contextmenu)

        delete = QShortcut(QKeySequence("Delete"), self)
        delete.activated.connect(self.remove_selected_link)

    def updateCompleter(self):
        docs = list(map(lambda x: x, self.db.root.documents))

        start = '**Feature name:**'
        end = "**Feature requirement:**"
        texts = []
        for doc in docs:
            for item in doc.items:
                dt = item.text
                uid = str(item.uid)
                if start in dt and end in dt:
                    text = dt[dt.find(start) + len(start):dt.rfind(end)].strip()
                    text = uid + ' | ' + text
                else:
                    text = uid
                texts.append(text)
                self.completerdict[text] = uid
        model = QStringListModel()
        model.setStringList(texts)
        self.completer.setModel(model)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

    def contextmenu(self, pos):
        if self.db is None:
            return
        if self.currentuid is None:
            return
        menu = QMenu(parent=self)
        si = self.listview.selectedIndexes()


        if len(si) == 0:
            return

        item = self.model.itemFromIndex(si[0])
        data = item.data()
        if type(data) is not tuple:
            return

        target = data[2]
        flags = data[3]
        is_suspect = 'suspect' in flags

        act = menu.addAction(self.icons.ArrowForward, 'Go to {}'.format(str(target.uid)))
        act.triggered.connect(lambda: self.goto(target.uid))
        if target.uid in self.db.find(self.currentuid).links:
            act = menu.addAction('Mark link as reviewed')
            act.setEnabled(is_suspect)
            act.triggered.connect(lambda: self.review_link(target.uid))
        else:
            act = menu.addAction("Can't mark child links as reviewed")
            act.setEnabled(False)
        act = menu.addAction(self.icons.DialogCloseButton, 'Remove link')
        act.triggered.connect(self.remove_selected_link)
        menu.popup(self.mapToGlobal(pos))

    def connectdb(self, db):
        self.db = db
        self.updateCompleter()

    def read(self, uid):
        if self.db is None:
            return
        self.currentuid = None

        data = self.db.find(uid)
        self.model.clear()
        for link in data.links:
            d = self.db.find(str(link))
            item = QStandardItem(str(link))
            target = self.db.find(link)
            flags = set()
            if target is None:
                flags.add('broken')
            elif link.stamp != target.stamp():
                flags.add('suspect')
            item.setData((True, link, d, flags))
            item.setEditable(False)
            self.model.appendRow(item)

        clinks = data.find_child_links()
        for clink in clinks:
            d = self.db.find(str(clink))
            item = QStandardItem(str(clink))
            item.setData((False, clink, d, set()))
            item.setEditable(False)
            self.model.appendRow(item)

        while self.model.rowCount() < 5:
            item = QStandardItem()
            item.setEditable(False)
            item.setSelectable(False)
            self.model.appendRow(item)

        self.currentuid = uid

    def remove_selected_link(self):
        if self.db is None:
            return
        if self.currentuid is None:
            return
        si = self.listview.selectedIndexes()

        if len(si) == 0:
            return

        item = self.model.itemFromIndex(si[0])
        data = item.data()
        if type(data) is not tuple:
            return
        uid = data[1]
        if uid not in self.db.find(self.currentuid).links:
            return

        self.db.root.unlink_items(self.currentuid, uid)
        self.read(self.currentuid)

    def review_link(self, uid):
        if self.db is None:
            return
        if self.currentuid is None:
            return
        cur = self.db.find(self.currentuid)
        for link in cur.links:
            if link == uid:
                link.stamp = self.db.find(uid).stamp()
        cur.save()
        self.read(self.currentuid)

    def goto(self, uid):
        if self.gotoclb:
            self.gotoclb(uid)

    def setlinkingitem(self, uid):
        if uid != self.currentuid and uid:
            parentuid = self.currentuid
            uid = str(uid)
            self.model.blockSignals(True)
            self.db.root.link_items(self.currentuid, uid)

            self.model.blockSignals(False)
            self.read(parentuid)
            return parentuid

    def createlinkingitem(self, text):
        uid = self.completerdict[text]
        self.setlinkingitem(uid)
