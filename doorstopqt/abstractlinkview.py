from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .icon import Icon
from .customcompleter import CustomQCompleter
from .searchlayout import SearchLayout
from .nameregex import Nameregex

'''
AbstractLinkView is used as a common ground for linkview and linkotherview.
'''


class AbstractLinkView(QWidget):
    def __init__(self, itemview, attribview, header="", iconcolor=None):
        super().__init__()
        self.vbox = QVBoxLayout()
        self.listview = QListView()
        self.icons = Icon(iconcolor)
        self.db = None

        self.locked = False
        self.currentitemedit = None
        self.currentindexedit = None
        self.markdownview = itemview.markdownview
        self.attribview = attribview
        self.attribview.readlinkview = self.read
        self.itemview = itemview

        self.completer = CustomQCompleter()

        self.linkentry = SearchLayout('Add item')
        self.linkentry.searchbox.setCompleter(self.completer)

        self.label = QLabel('Link ' + header)
        self.vbox.addWidget(self.label)
        self.vbox.addLayout(self.linkentry)
        self.vbox.addWidget(self.listview)
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbox)
        self.completerdict = {}
        self.gotoclb = None

        self.listview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listview.customContextMenuRequested.connect(self.contextmenu)
        self.completer.activated.connect(self.createlinkingitem)
        self.nameregex = Nameregex()

        def clicked(index):
            item = self.model.itemFromIndex(index)
            if item.isEditable():
                self.currentitemedit = item
                self.currentindexedit = index
                self.setlock(True)
                self.edit(index)
            else:
                self.setlock(False)

        self.listview.clicked.connect(clicked)

        def dblclicked(index):
            item = self.model.itemFromIndex(index)
            data = item.data()
            if data is None or item.isEditable():
                return
            if type(data) is str:
                uid = data.split(' ', 1)[0]
            elif type(data) is tuple:
                uid = data[1]
            self.goto(uid)
        self.listview.doubleClicked.connect(dblclicked)

    def createlinkingitem(self, text):
        if text not in self.completerdict:
            return
        uid = self.completerdict[text]
        self.setlock(True)
        self.setlinkingitem(uid)
        self.itemview.updatelastupdated()

    def setlock(self, lock):
        self.locked = lock

    def updateCompleter(self, docs):
        texts = []
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
                self.completerdict[text] = uid
        model = QStringListModel()
        model.setStringList(texts)
        self.completer.setModel(model)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)



