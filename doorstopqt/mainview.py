#!/usr/bin/env python

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from doorstopqt.version import VERSION
from doorstopqt.fullview import ReqView, TestView, ProductView
import resources  # resources fetches icons (don't remove)
from doorstopqt.stylesheetdark import stylesheet as stylesheetdark
from doorstopqt.stylesheetwhite import stylesheet as stylesheetwhite
from pathlib import Path
import sys
import os
from .initdirectoriesview import InitDirectoriesView
import json
from json import JSONDecodeError

class CustomSplitter(QSplitter):
    """
    Custom splitter to be able to move buttons when resizing the window.
    """
    def __init__(self):
        super(CustomSplitter, self).__init__()
        self.movebuttons = None
        self.setdarkstylesheet()


    def resizeEvent(self, a0: QResizeEvent) -> None:
        if self.movebuttons:
            self.movebuttons()
        super().resizeEvent(a0)

    def setwhiteStylesheet(self):
        self.setStyleSheet(stylesheetwhite)

    def setdarkstylesheet(self):
        self.setStyleSheet(stylesheetdark)

    def setdefaultstylesheet(self):
        self.setStyleSheet("")


def getlabel(showhide, view):
    return '{} {} {}'.format(showhide, view.header, 'view')


def sethideshowlabels(view, action):
    if not view.isHidden():
        view.hide()
        action.setText(getlabel('Show', view))
    else:
        view.show()
        action.setText(getlabel('Hide', view))


def inithideshow(view, menu):
    if not view.isHidden():
        productaction = menu.addAction(getlabel('Hide', view))
        productaction.triggered.connect(lambda: sethideshowlabels(view, productaction))

    else:
        productaction = menu.addAction(getlabel('Show', view))
        productaction.triggered.connect(lambda: sethideshowlabels(view, productaction))


def getdatabasedict(databasestextfile):
    if os.path.isfile(databasestextfile):
        file_obj = open(databasestextfile, 'r')
        try:
            databasedict = json.load(file_obj)
            return databasedict
        except JSONDecodeError:
            return


def main():

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    splitter = CustomSplitter()

    screen_resolution = app.desktop().screenGeometry()
    screenwidth, screenheight = screen_resolution.width(), screen_resolution.height()
    width = int(screenwidth*12/16)
    height = int(screenheight*12/16)

    splitter.resize(width, height)

    splitter.setWindowTitle('doorstop-qt {}'.format(VERSION))

    databasestextfile = Path(os.getcwd(), 'doorstopqt_databases.json')
    if not os.path.isfile(databasestextfile):
        initdirectories = InitDirectoriesView(databasestextfile, stylesheetdark)
        closeprogram = initdirectories.exec()
        if closeprogram:
            sys.exit()

    databasedict = getdatabasedict(databasestextfile)
    headers = [('Requirement', ReqView), ('Test', TestView), ('Product', ProductView)]
    views = []
    viewsdict = {}
    for header in headers:
        name = header[0]
        viewtype = header[1]
        if name in databasedict:
            view = viewtype()
            views.append(view)
            viewsdict[name] = view

    #reqview = ReqView()
    #testview = TestView()
    #productview = ProductView()

    #views = [reqview, testview, productview]
    linkviews = {}
    for view in views:
        linkviews[view.header] = [view.reqtestlinkview, view.reqtestlinkview2]

    for i, view in enumerate(views):
        view.tree.clipboard = lambda x: app.clipboard().setText(x)
        view.database = view.calldatabase(view.header)
        view.database.add_listeners([view.attribview, view.linkview, view.reqtestlinkview, view.reqtestlinkview2,
                                     view.tree, view.docview, view.itemview])
        view.docview.reloaddatabase = view.database.opennewdatabase

        def modeclb(editmode):
            if editmode:
                view.attribview.showref(True)
            else:
                view.attribview.showref(False)
        view.markdownview.modeclb = modeclb

        for v in view.otherheaders:
            lv = linkviews[v.capitalize()][0]
            del linkviews[v.capitalize()][0]
            view.database.add_other_listeners(lv)

        view.reqtestlinkview.gotoclb = viewsdict[view.otherheaders[0].capitalize()].selectfunc
        view.reqtestlinkview2.gotoclb = viewsdict[view.otherheaders[1].capitalize()].selectfunc

        splitter.addWidget(view)
    #reqview.database.add_other_listeners([testview.reqtestlinkview, productview.reqtestlinkview])
    #testview.database.add_other_listeners([reqview.reqtestlinkview, productview.reqtestlinkview2])
    #productview.database.add_other_listeners([reqview.reqtestlinkview2, testview.reqtestlinkview2])

    #reqview.reqtestlinkview.gotoclb = testview.selectfunc
    #testview.reqtestlinkview.gotoclb = reqview.selectfunc
    #productview.reqtestlinkview.gotoclb = reqview.selectfunc

    #reqview.reqtestlinkview2.gotoclb = productview.selectfunc
    #testview.reqtestlinkview2.gotoclb = productview.selectfunc
    #productview.reqtestlinkview2.gotoclb = testview.selectfunc
    if 'test' in viewsdict and 'product' in viewsdict:
        viewsdict['test'].itemview.applytootheritem = viewsdict['product'].reqtestlinkview2.updatedata

    mainMenu = QMenuBar()
    optionsMenu = mainMenu.addMenu('Options')
    changestylesheetmenu = optionsMenu.addMenu('Change theme')
    darktheme = changestylesheetmenu.addAction("Dark theme")
    whitetheme = changestylesheetmenu.addAction("White theme")
    darktheme.triggered.connect(splitter.setdarkstylesheet)
    whitetheme.triggered.connect(splitter.setwhiteStylesheet)

    showhidemenu = optionsMenu.addMenu('Show/hide views')

    splitter.addWidget(mainMenu)
    #splitter.addWidget(reqview)
    #splitter.addWidget(testview)
    #splitter.addWidget(productview)

    splitter.setOrientation(Qt.Vertical)
    splitter.setStretchFactor(0, 2)

    splitter.show()
    for view in views:
        view.movebuttons()
        inithideshow(view, showhidemenu)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
