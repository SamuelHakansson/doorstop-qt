from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .icon import Icon
import os
import json
from json import JSONDecodeError
from pathlib import Path


class InitDirectoriesView(QDialog):
    def __init__(self, databasepath, databasenames, style=''):
        super(InitDirectoriesView, self).__init__()
        self.setWindowTitle('Select folder')
        self.databasepath = databasepath
        self.icons = Icon()
        self.setStyleSheet(style)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.exiticon = self.icons.fromTheme('edit-clear-all')
        self.exitbutton = QPushButton(self.exiticon, 'Exit')
        self.buttons = DirectoryButtons(self.icons, self.databasepath, databasenames, self)
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
    def __init__(self, icons, databasepath, databasenames, initview=None):
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
        self.nochanges = False
        if initview is None:
            self.openpathdialog(databasenames)

        for name in buttonnames:
            self.createbutton(name, databasenames)

    def createbutton(self, name, databasenames):
        column = QWidget()
        vbox = QVBoxLayout()
        column.setLayout(vbox)
        button = QPushButton(self.foldericon, '')
        button.setFixedSize(self.size)
        button.setIconSize(self.size)
        vbox.addWidget(button)
        vbox.addWidget(QLabel(name))
        self.layout.addWidget(column)
        button.clicked.connect(lambda: self.openpathdialog(databasenames))

    def openpathdialog(self, databasenames):

        dialog = QFileDialog(None, "Select directory for the repository. "
                                   "Select an empty folder if you want to start from scratch.")
        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec_() == QDialog.Accepted:
            path = dialog.selectedFiles()[0]
        else:
            self.nochanges = True
            if self.initview:
                self.initview.exit()
            return

        for name in os.listdir(path):
            for dbname in databasenames:
                if dbname.lower() in name:
                    directory = QDir(path)
                    directory.cd(name)
                    dbpath = directory.path()
                    self.writetojsonfile(dbname, dbpath, self.databasepath)
        if self.initview:
            self.initview.close()

    def writetojsonfile(self, name, path, databasestextfile):
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

    def exec(self):
        return self.nochanges





