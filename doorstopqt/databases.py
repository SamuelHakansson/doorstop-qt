import os
import doorstop
from pathlib import Path


class ReqDatabase(object):
    def __init__(self):
        self.listeners = []
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

    def reload(self):
        self.root = doorstop.core.builder.build()
        for l in self.listeners:
            l.connectdb(self)

    def find(self, uid):
        for document in self.root:
            for item in document:
                if str(item.uid) == uid:
                    return item
        return None

    def remove(self, uid):
        item = self.find(uid)
        item.delete()
        self.reload()


class TestDatabase(ReqDatabase):
    def __init__(self):
        currentdir = os.getcwd()
        os.chdir("..")
        self.folder = '/tests/'
        self.path = Path(os.getcwd() + self.folder)
        super().__init__()
        os.chdir(currentdir)

    def reload(self):
        self.root = doorstop.core.builder.build(root=self.path)
        for l in self.listeners:
            l.connectdb(self)
