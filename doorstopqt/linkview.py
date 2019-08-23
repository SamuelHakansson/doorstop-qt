from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .abstractlinkview import AbstractLinkView
from .linkitemmodel import LinkItemModel


class LinkView(AbstractLinkView):
    def __init__(self, itemview, attribview, header=""):
        super(LinkView, self).__init__(itemview, attribview, header=header)

        self.linkentry.searchbox.setPlaceholderText('Add parent link')

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

        act = menu.addAction(self.icons.ArrowForward, 'Go to {}'.format(str(target.uid))
                                                                        if target is not None else "Link is broken, can't go to it")
        act.triggered.connect(lambda: self.goto(target.uid) if target is not None else None)

        currentitem = self.db.find(self.currentuid)
        if target is not None:
            if target.uid in currentitem.links:
                act = menu.addAction('Mark link as reviewed')
                act.setEnabled(is_suspect)
                act.triggered.connect(lambda: self.review_link(target.uid))
            else:
                act = menu.addAction("Can't mark child links as reviewed")
                act.setEnabled(False)
        else:
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
        nrfinelinks = 0
        for link in data.links:
            d = self.db.find(str(link))
            item = QStandardItem(str(link))
            target = self.db.find(link)
            flags = set()
            if target is None:
                flags.add('broken')
            elif link.stamp != target.stamp():
                flags.add('suspect')
            else:
                nrfinelinks += 1
            item.setData((True, link, d, flags))
            item.setEditable(False)
            self.model.appendRow(item)
        if nrfinelinks == len(data.links):
            data.review()

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
        self.attribview.read(uid)

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
        if self.db.find(uid) is None:
            self.db.find(self.currentuid).unlink(uid)
        else:
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

    def updateCompleter(self):
        docs = list(map(lambda x: x, self.db.root.documents))
        super(LinkView, self).updateCompleter(docs)

    def goto(self, uid):
        if self.gotoclb:
            self.gotoclb(uid)


