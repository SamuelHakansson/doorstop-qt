from PyQt5.QtCore import *
from PyQt5.QtGui import *
from .nameregex import Nameregex


class LinkItemModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(LinkItemModel, self).__init__(parent)
        self.nameregex = Nameregex()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            item = self.itemFromIndex(index)
            data = item.data()
            if type(data) is str:
                return data
            elif type(data) is tuple:
                is_parent_link = data[0]
                uid = data[1]
                target = data[2]
                flags = data[3]
                title = ''
                if target is not None:
                    title = self.nameregex.gettitle(target.text)
                if 'broken' in flags:
                    extra = '[broken] '
                elif 'suspect' in flags:
                    extra = '[needs review] '
                else:
                    extra = ''
                text = extra + str(uid) + ' | ' + title
                if is_parent_link:
                    return '→ ' + text
                else:
                    return '← ' + text
            return ''

        return super(LinkItemModel, self).data(index, role)


class SimpleLinkItemModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(SimpleLinkItemModel, self).__init__(parent)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            item = self.itemFromIndex(index)
            data = item.data()
            if type(data) is str:
                uid = data
                return str(uid)
        return super(SimpleLinkItemModel, self).data(index, role)


