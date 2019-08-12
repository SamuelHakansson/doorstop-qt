import os
import doorstop
from pathlib import Path


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
    def __init__(self, folder):
        currentdir = os.getcwd()
        os.chdir("..")
        self.folder = folder
        self.path = Path(os.getcwd(), self.folder)

        if not os.path.exists(self.path):
            os.makedirs(self.path)
        os.chdir(self.path)
        if os.system('git rev-parse') != 0:
            os.system("git init .")
        os.chdir("..")
        super().__init__()
        os.chdir(currentdir)

    def reload(self):
        super(OtherDatabase, self).reload(root=self.path)


class TestDatabase(OtherDatabase):
    def __init__(self):
        self.folder = 'tests'
        super().__init__(self.folder)


class ProductDatabase(OtherDatabase):
    def __init__(self):
        self.folder = 'products'
        super().__init__(self.folder)


