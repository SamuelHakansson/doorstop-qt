from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .abstractlinkview import AbstractLinkView
from .linkitemmodel import SimpleLinkItemModel
from doorstop.core import Tree, Document, builder
from pathlib import Path


class LinkReqAndTestView(AbstractLinkView):
    def __init__(self, itemview, attribview, key, ownkey, header=""):
        super(LinkReqAndTestView, self).__init__(itemview, attribview, header=header)
        self.header = header
        self.key = key
        self.ownkey = ownkey
        self.otherdb = None
        self.model = SimpleLinkItemModel()
        self.listview.setModel(self.model)
        self.linkentry.setPlaceholderText('{} {} {}'.format('<Click here to add', self.header, 'link>'))
        self.attribview.getotherdbitems = self.getpublishtree
        self.currentuid = None
        self.INPUTVARIABLES = 'inputvariables'
        self.EXPECTEDRESULTS = 'expectedresults'
        self.itemview = itemview

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

        #self.listview.currentChanged.connect(self.updateexpectedresults)
        self.listview.selectionModel().selectionChanged.connect(self.showexpectedresults)


    def connectdb(self, db):
        self.db = db
        self.read(self.currentuid)

    def read(self, uid):
        if uid is None:
            return
        if self.db is None:
            return
        if self.locked:
            return
        self.currentuid = None
        self.model.clear()
        item = self.db.find(uid)
        if item is None:
            return
        if self.key in item.data:
            for link in item.data[self.key]:
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

    def connectotherdb(self, db):
        self.otherdb = db
        self.updateCompleter()
        self.read(self.currentuid)

    def goto(self, uid, readcurrent=False):
        if self.gotoclb:
            self.gotoclb(uid, readcurrent)

    def removelink(self, dbitem, uid):
        if not dbitem:
            return
        if self.key in dbitem.data:
            tmp = dbitem.data[self.key]
            if uid in tmp:
                tmp.remove(uid)
            dbitem.set(self.key, tmp)

    def removeotherlink(self, dbitem, uid):
        if not dbitem:
            return
        if self.ownkey in dbitem.data:
            tmp = dbitem.data[self.ownkey]
            if uid in tmp:
                tmp.remove(uid)
            dbitem.set(self.ownkey, tmp)

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
            itemother.set(self.ownkey, self.getlinkdata(itemother) + [uidthis])
        if self.header == 'test' and self.ownkey == 'linkedproducts':
            self.settoitem(itemthis, itemother, key=self.INPUTVARIABLES)
            self.settoitem(itemthis, itemother, key=self.EXPECTEDRESULTS)

        self.db.reload()
        self.otherdb.reload()

    def settoitem(self, itemthis, itemother, key):
        vars = []
        if key in itemother.data:
            vars = itemother.data[key]
        prevdata = []
        if key in itemthis.data:
            prevdata = itemthis.data[key]
        itemthis.set(key, prevdata + vars)

    def getpublishtree(self):
        items = []
        item = self.db.find(self.currentuid)
        if self.key in item.data:
            for linkuid in item.data[self.key]:
                linkitem = self.otherdb.find(linkuid)
                items.append(linkitem)
        return self.otherdb.root, items

    def updatedata(self, uid):
        item = self.otherdb.find(uid)
        self.updateinputvariables(item)

        self.db.reload()

    def updateinputvariables(self, item):
        if self.ownkey not in item.data:
            return
        if self.INPUTVARIABLES not in item.data:
            return
        links = item.data[self.ownkey]
        inputvars = item.data[self.INPUTVARIABLES]
        for link in links:
            it = self.db.find(link)
            prevdata = it.data[self.INPUTVARIABLES]
            newinputvars = prevdata
            for var in inputvars:
                if var[0] not in [x[0] for x in prevdata]:
                    newinputvars.append(var)
            it.set(self.INPUTVARIABLES, newinputvars)

    def updateexpectedresults(self, item):
        if self.ownkey not in item.data:
            return
        if self.EXPECTEDRESULTS not in item.data:
            return
        links = item.data[self.ownkey]
        itemresults = item.data[self.EXPECTEDRESULTS]
        for link in links:
            it = self.db.find(link)
            linkexpectedresults = [item for item in it.data[self.EXPECTEDRESULTS] if item[0] == link][0]
            for i, pair in enumerate(itemresults):
                if pair[0] == it.uid and (pair[1] == '' or pair[1] in linkexpectedresults):
                    del itemresults[i]
                    itemresults.insert(i, linkexpectedresults)
            it.set(self.EXPECTEDRESULTS, itemresults)

    def showexpectedresults(self, selection):
        if len(selection.indexes()) > 0:
            uid = selection.indexes()[0].data()
            self.itemview.showexpectedresults(uid)

