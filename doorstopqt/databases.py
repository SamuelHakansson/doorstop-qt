import os
import doorstop
from pathlib import Path
from PyQt5.QtWidgets import *
import json


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
        self.path = os.getcwd()
        '''
        print('cwd', os.getcwd(), flush=True)
        databasestextfile = Path(os.getcwd(), 'databases.json')
        print(databasestextfile, flush=True)
        if os.path.isfile(databasestextfile):
            file_obj = open(databasestextfile, 'r')
            databasedict = json.load(file_obj)
            if name in databasedict:
                self.path = Path(databasedict[name])
            else:
                self._writetojsonfile(databasestextfile, name)
        else:
            self._writetojsonfile(databasestextfile, name)
        '''
        currentdir = os.getcwd()

        os.chdir("..")
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        os.chdir(self.path)
        if os.system('git rev-parse') != 0:
            os.system("git init .")
        os.chdir("..")
        super().__init__()
        os.chdir(currentdir)

    def reload(self, root=None):
        if root:
            self.path = root
        super(OtherDatabase, self).reload(root=self.path)

    def _openfiledialog(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec_() == QDialog.Accepted:
            path = dialog.selectedFiles()[0]
        return path

    def _writetojsonfile(self, databasestextfile, name):
            self.path = self._openfiledialog()
            file_obj = open(databasestextfile, 'w+')
            databasedict = json.load(file_obj)
            print(databasedict, flush=True)
            if not databasedict:
                databasedict = {name: self.path}
            else:
                databasedict[name] = self.path
            json.dump(databasedict, file_obj)

    def opennewdatabase(self):
        folder = self._openfiledialog()
        self.reload(folder)


