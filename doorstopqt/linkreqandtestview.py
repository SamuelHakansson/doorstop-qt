from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .abstractlinkview import AbstractLinkView
from .linkitemmodel import SimpleLinkItemModel


class LinkReqAndTestView(AbstractLinkView):
    def __init__(self, markdownview, attribview, header=""):
        super(LinkReqAndTestView, self).__init__(markdownview, attribview, header=header)
        self.key = 'linkedrequirements'
        self.otherdb = None
        self.model = SimpleLinkItemModel()
        self.listview.setModel(self.model)
        self.linkentry.setPlaceholderText('{} {} {}'.format('<Click here to add', header, 'link>'))

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
            for link in item._data[self.key]:
                item = QStandardItem(str(link))
                item.setData(str(link))
                item.setEditable(False)
                self.model.appendRow(item)

        while self.model.rowCount() < 5:
            item = QStandardItem()
            item.setEditable(False)
            item.setSelectable(False)
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
        otherdbitem = self.otherdb.find(data)
        self.removelink(dbitem, data)
        self.removelink(otherdbitem, str(dbitem.uid))

        self.read(self.currentuid)

    def updateCompleter(self):
        docs = list(map(lambda x: x, self.otherdb.root.documents))
        super(LinkReqAndTestView, self).updateCompleter(docs)

    def setotherdb(self, db):
        self.otherdb = db
        self.updateCompleter()

    def goto(self, uid, readcurrent=False):
        if self.gotoclb:
            self.gotoclb(uid, readcurrent)

    def removelink(self, dbitem, data):
        if not dbitem:
            return
        if self.key in dbitem._data:
            tmp = dbitem._data[self.key]
            tmp.remove(data)
            dbitem.set(self.key, tmp)

    def setlinkingitem(self, uid):
        if self.locked and uid != self.currentuid and uid:
            uidthis = self.currentuid

            self.linkitems(uidthis, uidother=uid)
            self.setlock(False)
            self.read(uidthis)
            return uid

    def getlinkdata(self, item):
        if self.key in item._data:
            return item._data[self.key]
        else:
            return []

    def linkitems(self, uidthis, uidother):
        itemthis = self.db.find(uidthis)
        itemother = self.otherdb.find(uidother)
        if uidother not in self.getlinkdata(itemthis):
            itemthis.set(self.key, self.getlinkdata(itemthis) + [uidother])
        if uidthis not in self.getlinkdata(itemother):
            itemother.set(self.key, self.getlinkdata(itemother) + [uidthis])
