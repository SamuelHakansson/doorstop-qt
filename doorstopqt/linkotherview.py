from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .abstractlinkview import AbstractLinkView
from .linkitemmodel import SimpleLinkItemModel
from .lastupdatedtext import LastUpdatedText


class LinkOtherView(AbstractLinkView):
    def __init__(self, itemview, attribview, key, ownkey, header="", changeexpectedresults=False, iconcolor=None):
        super(LinkOtherView, self).__init__(itemview, attribview, header=header, iconcolor=iconcolor)
        self.header = header
        self.key = key
        self.ownkey = ownkey
        self.otherdb = None
        self.model = SimpleLinkItemModel()
        self.listview.setModel(self.model)
        self.linkentry.searchbox.setPlaceholderText('{} {} {}'.format('Add', self.header, 'link'))
        self.attribview.getotherdbitems = self.getpublishtree
        self.currentuid = None
        self.INPUTVARIABLES = 'inputvariables'
        self.EXPECTEDRESULTS = 'expectedresults'
        self.itemview = itemview
        self.lastupdated = LastUpdatedText()

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

        if changeexpectedresults:
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
                text = ''
                
                if self.otherdb:
                    linkitem = self.otherdb.find(link)
                    if linkitem:
                        start = '**Feature name:**'
                        end = "**Feature requirement:**"
                        dt = linkitem.text
                        if start in dt and end in dt:
                            text = ' | ' + dt[dt.find(start) + len(start):dt.rfind(end)].strip()

                item = QStandardItem(str(link))
                item.setData(str(link) + text)
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
        act.triggered.connect(lambda: self.goto(self.getuidfromguiitem(data)))

        act = menu.addAction(self.icons.DialogCloseButton, 'Remove link')
        act.triggered.connect(self.remove_selected_link)
        menu.popup(self.mapToGlobal(pos))

    def getuidfromguiitem(self, data):
        uid = data.split(' ', 1)[0]
        return uid

    def remove_selected_link(self):
        if self.db is None:
            return
        if self.currentuid is None:
            return
        si = self.listview.selectedIndexes()

        if len(si) == 0:
            return

        item = self.model.itemFromIndex(si[0])
        data = self.getuidfromguiitem(item.data())

        dbitem = self.db.find(self.currentuid)
        otherdbitem = self.otherdb.find(data)
        self.removelink(dbitem, data)
        self.removeotherlink(otherdbitem, str(dbitem.uid))

        self.read(self.currentuid)

    def updateCompleter(self):
        docs = list(map(lambda x: x, self.otherdb.root.documents))
        super(LinkOtherView, self).updateCompleter(docs)

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
        self.otherdb.reload()

    def setlinkingitem(self, uid):
        if self.locked and uid != self.currentuid and uid:
            uidthis = self.currentuid

            self.linkitems(uidthis, uidother=uid)
            self.setlock(False)
            self.read(uidthis)
            return uid

    def getlinkdata(self, item, key):
        if key in item._data:
            return item._data[key]
        else:
            return []

    def linkitems(self, uidthis, uidother):
        itemthis = self.db.find(uidthis)
        itemother = self.otherdb.find(uidother)
        if uidother not in self.getlinkdata(itemthis, self.key):
            itemthis.set(self.key, self.getlinkdata(itemthis, self.key) + [uidother])
        if uidthis not in self.getlinkdata(itemother, self.ownkey):
            itemother.set(self.ownkey, self.getlinkdata(itemother, self.ownkey) + [uidthis])
        if self.header == 'test' and self.ownkey == 'linkedproducts':
            self.settoitem(itemthis, itemother, key=self.INPUTVARIABLES)
            self.settoitem(itemthis, itemother, key=self.EXPECTEDRESULTS)

        if self.header == 'product' and self.ownkey == 'linkedtests':
            self.settoitem(itemother, itemthis, key=self.INPUTVARIABLES)
            self.settoitem(itemother, itemthis, key=self.EXPECTEDRESULTS)

        itemother.set(self.lastupdated.name, self.lastupdated.getcurrenttime())
        self.db.reload()
        self.otherdb.reload()

    def settoitem(self, itemthis, itemother, key):
        vars = []
        if key in itemother.data:
            vars = itemother.data[key]
        prevdata = []
        if key in itemthis.data:
            prevdata = itemthis.data[key]
            for i, entry in enumerate(prevdata):
                for varpair in vars:
                    if entry[0] == varpair[0]:
                        del prevdata[i]
        if prevdata + vars:
            itemthis.set(key, prevdata + vars)

    def getpublishtree(self, uid=None):
        items = []
        if uid is None:
            uid = self.currentuid
        item = self.db.find(uid)
        if self.key in item.data:
            for linkuid in item.data[self.key]:
                linkitem = self.otherdb.find(linkuid)
                items.append(linkitem)
        return self.otherdb.root, items, uid

    def updatedata(self, uid):
        item = self.otherdb.find(uid)
        self.updateinputvariables(item)
        self.updateexpectedresults(item)
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
            if self.INPUTVARIABLES in it.data:
                prevdata = it.data[self.INPUTVARIABLES]
            else:
                prevdata = []
            newinputvars = prevdata
            for i, var in enumerate(inputvars):
                name = var[0]
                if name not in [x[0] for x in prevdata]:
                    newinputvars.append(var)
                else:
                    del newinputvars[i]
                    newinputvars.insert(i, var)
            it.set(self.INPUTVARIABLES, newinputvars)

    def updateexpectedresults(self, miditem):
        if self.ownkey not in miditem.data:
            return
        if self.EXPECTEDRESULTS not in miditem.data:
            return
        links = miditem.data[self.ownkey]
        miditemresults = miditem.data[self.EXPECTEDRESULTS][0]
        for link in links:
            newitem = self.db.find(link)
            if self.EXPECTEDRESULTS in newitem.data:
                expres = newitem.data[self.EXPECTEDRESULTS]
                for i, pair in enumerate(expres):
                    if pair[0] == str(miditem.uid) and (pair[1] == '' or pair[1] in miditemresults[1]):
                        del expres[i]
                        expres.insert(i, miditemresults)

            else:
                expres = [miditemresults]
            newitem.set(self.EXPECTEDRESULTS, expres)

    def showexpectedresults(self, selection):
        if len(selection.indexes()) > 0:
            uid = selection.indexes()[0].data()
        else:
            uid = None
        self.itemview.showexpectedresults(uid)


