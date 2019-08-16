import os
import doorstop
from pathlib import Path
from PyQt5.QtWidgets import *
import json
from json import JSONDecodeError


class ReqDatabase(object):
    def __init__(self):
        self.listeners = []
        self.other_listeners = []
        self.root = None
        self.reload()

    def add_listeners(self, l):
        if type(l) is list:
            for listener in l:
                listener.connectdb(self)
                self.listeners.append(listener)
        else:
            l.connectdb(self)
            self.listeners.append(l)

    def add_other_listeners(self, l):
        if type(l) is list:
            for listener in l:
                listener.connectotherdb(self)
                self.other_listeners.append(listener)
        else:
            l.connectotherdb(self)
            self.other_listeners.append(l)

    def reload(self, root=None):
        self.root = doorstop.core.builder.build(root=root)
        for l in self.listeners:
            l.connectdb(self)
        for ol in self.other_listeners:
            ol.connectotherdb(self)

    def find(self, uid):
        for document in self.root:
            for item in document:
                if str(item.uid) == uid:
                    return item
        return None

    def remove(self, uid):
        item = self.find(uid)
        if item:
            item.delete()
            self.reload()


class OtherDatabase(ReqDatabase):
    def __init__(self, name=None):
        self.name = name

        databasestextfile = Path(os.getcwd(), 'doorstopqt_databases.json')
        self.path = self.finddatabasepath(databasestextfile)
        if self.path is None:
            self.path = self._openfiledialog()

        self._writetojsonfile(databasestextfile)

        currentdir = os.getcwd()
        self.initgit()
        super().__init__()
        os.chdir(currentdir)

    def reload(self, root=None):
        super(OtherDatabase, self).reload(root=self.path)

    def _openfiledialog(self):
        dialog = QFileDialog(None, "{} {}{} {}".format("Select Directory for", self.name.lower(), ".",
                                                     "Select an empty folder if you want to start from scratch."))
        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec_() == QDialog.Accepted:
            path = dialog.selectedFiles()[0]
        else:
            path = None
        return path

    def _writetojsonfile(self, databasestextfile):
        if os.path.isfile(databasestextfile):
            file_obj = open(databasestextfile, 'r')
            try:
                databasedict = json.load(file_obj)
                databasedict[self.name] = self.path
            except JSONDecodeError:
                databasedict = {self.name: self.path}
        else:
            databasedict = {self.name: self.path}

        file_obj_wr = open(databasestextfile, 'w+')

        json.dump(databasedict, file_obj_wr)

    def finddatabasepath(self, databasestextfile):
        if os.path.isfile(databasestextfile):
            file_obj = open(databasestextfile, 'r')
            try:
                databasedict = json.load(file_obj)
                if self.name in databasedict:
                    return databasedict[self.name]
            except JSONDecodeError:
                return

    def opennewdatabase(self):
        folder = self._openfiledialog()
        if folder:
            self.path = folder
            self.initgit()
            self.reload(folder)

    def initgit(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        os.chdir(self.path)
        if os.system('git rev-parse') != 0:
            os.system("git init .")



