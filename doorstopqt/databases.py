import os
import doorstop
from pathlib import Path
from PyQt5.QtWidgets import *
import json
from json import JSONDecodeError


class ReqDatabase(object):
    def __init__(self, path=None):
        self.listeners = []
        self.other_listeners = []
        self.root = None
        self.reload(path)

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

    def reload(self, path=None):
        self.root = doorstop.core.builder.build(root=Path(path))
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
    def __init__(self, path, databasestextfilepath, name=None):
        self.name = name
        self.databasestextfilepath = databasestextfilepath
        self.path = path
        if self.path is None:
            self.path = self._openfiledialog()
        self._writetojsonfile(self.databasestextfilepath)

        currentdir = os.getcwd()
        self.initgit()
        super().__init__(self.path)
        os.chdir(currentdir)

    def reload(self, path=None):
        super(OtherDatabase, self).reload(path=self.path)

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

    def opennewdatabase(self):
        folder = self._openfiledialog()
        if folder:
            self.path = folder
            self.initgit()
            self.reload(folder)
            self._writetojsonfile(self.databasestextfilepath)

    def initgit(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        os.chdir(self.path)
        if os.system('git rev-parse') != 0:
            os.system("git init .")



