from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .icon import Icon
import os
import json
from json import JSONDecodeError
from pathlib import Path


class InitDirectoriesView(QDialog):
    def __init__(self, databasepath, style=''):
        super(InitDirectoriesView, self).__init__()
        self.setWindowTitle('Select folder')
        self.databasepath = databasepath
        self.icons = Icon()
        self.setStyleSheet(style)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        #self.doneicon = self.icons.fromTheme('dialog-apply')
        self.exiticon = self.icons.fromTheme('edit-clear-all')
        self.exitbutton = QPushButton(self.exiticon, 'Exit')
        self.buttons = DirectoryButtons(self.icons, self.databasepath, self)
        self.layout.addWidget(self.buttons)
        vbox = QHBoxLayout()
        vbox.addWidget(self.exitbutton, alignment=Qt.AlignLeft)
        self.layout.addLayout(vbox)

        self.exitbutton.clicked.connect(self.exit)
        self.exitprogram = False

    def exit(self):
        self.exitprogram = True
        self.close()

    def exec(self):
        super(InitDirectoriesView, self).exec()
        return self.exitprogram


class DirectoryButtons(QWidget):
    def __init__(self, icons, databasepath, initview):
        super(DirectoryButtons, self).__init__()
        self.databasepath = databasepath
        self.initview = initview
        buttonnames = ['Repository']
        self.icons = icons
        self.foldericon = self.icons.fromTheme('folder-black')
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.size = QSize(150, 150)
        self.directories = []

        for name in buttonnames:
            self.createbutton(name)

    def createbutton(self, name):
        column = QWidget()
        vbox = QVBoxLayout()
        column.setLayout(vbox)
        button = QPushButton(self.foldericon, '')
        button.setFixedSize(self.size)
        button.setIconSize(self.size)
        vbox.addWidget(button)
        vbox.addWidget(QLabel(name))
        self.layout.addWidget(column)
        button.clicked.connect(lambda: self.openpathdialog())

    def openpathdialog(self):
        databasenames = ['Requirements', 'Tests', 'Products']
        dialog = QFileDialog(None, "Select Directory for the repository. "
                                   "Select an empty folder if you want to start from scratch.")
        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec_() == QDialog.Accepted:
            path = dialog.selectedFiles()[0]
        else:
            self.initview.exit()
            return
        for name in os.listdir(path):
            for dbname in databasenames:
                if dbname.lower() in name:
                    dbpath = str(Path(path, name))
                    self.writetojsonfile(dbname, dbpath, self.databasepath)
        self.initview.close()

    def writetojsonfile(self, name, path, databasestextfile):
        name = name[:-1]  # because views are named with an s in their fullview
        if os.path.isfile(databasestextfile):
            file_obj = open(databasestextfile, 'r')
            try:
                databasedict = json.load(file_obj)
                databasedict[name] = path
            except JSONDecodeError:
                databasedict = {name: path}
        else:
            databasedict = {name: path}

        file_obj_wr = open(databasestextfile, 'w+')

        json.dump(databasedict, file_obj_wr)





