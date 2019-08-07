from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .abstractlinkview import AbstractLinkView
from .linkitemmodel import LinkItemModel, SimpleLinkItemModel


class LinkReqAndTestView(AbstractLinkView):
    def __init__(self, markdownview, attribview, header=""):
        super(LinkReqAndTestView, self).__init__(markdownview, attribview, header=header)
        self.key = 'linkedrequirements'
        self.otherdb = None
        self.model = SimpleLinkItemModel()
        self.listview.setModel(self.model)

        def dataChanged(index):
            if self.db is None:
                return
            if self.currentuid is None:
                return

            item = self.model.itemFromIndex(index)
            uid = item.text()
            doc = self.db.find(uid)
            if doc is not None:
                self.setlock(False)

            self.goto(self.currentuid)

        self.model.dataChanged.connect(dataChanged)

        self.listview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listview.customContextMenuRequested.connect(self.contextmenu)

    def connectdb(self, db):
        self.db = db

    def read(self, uid):
        if self.db is None:
            return
        if self.locked:
            return
        self.currentuid = None
        self.model.clear()
        item = self.db.find(uid)
        if self.key in item._data:
            for link in item._data[self.key].split():
                item = QStandardItem(str(link))
                item.setData(str(link))
                item.setEditable(False)
                self.model.appendRow(item)
        self.currentuid = uid

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
        act = menu.addAction(self.icons.ArrowForward, 'Go to {}'.format(str(data)))
        act.triggered.connect(lambda: self.goto(data))

        act = menu.addAction(self.icons.DialogCloseButton, 'Remove link')
        act.triggered.connect(self.remove_selected_link)
        menu.popup(self.mapToGlobal(pos))

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

        dbitem = self.db.find(self.currentuid)
        print(dbitem, flush=True)
        if self.key in dbitem._data:
            newdata = dbitem._data[self.key].replace(data, "")
            print(newdata, flush=True)
            dbitem._data[self.key] = newdata
            dbitem.save()
        otherdbitem = self.otherdb.find(data)

        self.read(self.currentuid)


    def updateCompleter(self):
        docs = list(map(lambda x: x, self.otherdb.root.documents))
        super(LinkReqAndTestView, self).updateCompleter(docs)

    def setotherdb(self, db):
        self.otherdb = db
        self.updateCompleter()

    def goto(self, uid):
        if self.gotoclb:
            self.gotoclb(uid)


class LinkView(AbstractLinkView):
    def __init__(self, markdownview, attribview, header=""):
        super(LinkView, self).__init__(markdownview, attribview, header=header)

        self.linkentry.setPlaceholderText('<Click here to add parent link>')
        self.completer.activated.connect(self.createlinkingitem)
        self.model = LinkItemModel()
        self.listview.setModel(self.model)

        def dataChanged(index):
            if self.db is None:
                return
            if self.currentuid is None:
                return

            item = self.model.itemFromIndex(index)
            uid = item.text()
            doc = self.db.find(uid)
            if doc is not None:
                self.setlock(False)
                self.db.root.link_items(self.currentuid, uid)

            self.goto(self.currentuid)

        self.model.dataChanged.connect(dataChanged)


    def connectdb(self, db):
        self.db = db
        self.updateCompleter()

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


    def read(self, uid):

        if self.db is None:
            return
        if self.locked:
            return
        self.currentuid = None
        self.model.clear()
        data = self.db.find(uid)
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

    def setlinkingitem(self, uid):
        if self.locked and uid != self.currentuid and uid:
            parentuid = self.currentuid
            uid = str(uid)
            self.model.blockSignals(True)
            self.db.root.link_items(self.currentuid, uid)

            self.setlock(False)
            self.model.blockSignals(False)
            self.read(parentuid)
            return parentuid

    def createlinkingitem(self, text):
        uid = self.completerdict[text]
        self.setlock(True)
        self.setlinkingitem(uid)

    def updateCompleter(self):
        docs = list(map(lambda x: x, self.db.root.documents))
        super(LinkView, self).updateCompleter(docs)

    def goto(self, uid):
        if self.gotoclb:
            self.gotoclb(uid)


