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
from doorstopqt.initdirectoriesview import InitDirectoriesView
import json
from json import JSONDecodeError
from doorstopqt.icon import Icon
from argparse import ArgumentParser


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


def saveWindowSettings(splitter, id):
    settings = QSettings("Lab.gruppen", id)
    settings.setValue("geometry", splitter.saveGeometry())
    settings.setValue("windowState", splitter.saveState())

def loadWindowSettings(splitter, id):
    settings = QSettings("Lab.gruppen", id)
    if not settings.value("geometry"):
        return
    saved_geometry = settings.value("geometry")
    splitter.restoreGeometry(saved_geometry)
    saved_state = settings.value("windowState")
    splitter.restoreState(saved_state)


def getlabel(showhide, view):
    return '{} {} {}'.format(showhide, view.header, 'view')


def sethideshowlabels(view, action):
    if not view.isHidden():
        view.hide()
        saveshowhide(view, 'hide')
        action.setText(getlabel('Show', view))
    else:
        view.show()
        saveshowhide(view, 'show')
        action.setText(getlabel('Hide', view))


def inithideshow(view, menu):
    if not view.isHidden():
        productaction = menu.addAction(getlabel('Hide', view))
        productaction.triggered.connect(lambda: sethideshowlabels(view, productaction))

    else:
        productaction = menu.addAction(getlabel('Show', view))
        productaction.triggered.connect(lambda: sethideshowlabels(view, productaction))


def saveshowhide(view, showhide):
    showhidefile = Path(os.getcwd(), 'doorstopqt_showhideviews.json')
    data = getdictfromfile(showhidefile)
    if not data:
        data = {view.header: showhide}
    else:
        data[view.header] = showhide
    file = open(showhidefile, 'w+')
    json.dump(data, file)


def getdictfromfile(file):
    if os.path.isfile(file):
        file_obj = open(file, 'r')
        try:
            databasedict = json.load(file_obj)
            return databasedict
        except JSONDecodeError:
            return {}


def setupdirectories(app,  splitter, databasestextfile, mainmenu, showhidemenu, stylesheet=stylesheetdark):
    initdirectories = InitDirectoriesView(databasestextfile, stylesheet)
    if initdirectories.exec() is False:
        clearlayout(splitter)
        showhidemenu.clear()

        loadviews(app, splitter, databasestextfile, mainmenu, showhidemenu)


def clearlayout(splitter):
    for i in reversed(range(splitter.count())):
        splitter.widget(i).setParent(None)


def storeviews(mainsplitter):
    splitters = mainsplitter.findChildren(QSplitter)
    for id, splitter in enumerate(splitters):
        saveWindowSettings(splitter, str(id))


def main():

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    icons = Icon(Qt.black)
    doorstoplogo = icons.fromTheme('doorstop-qt-logo-smallest')
    app.setWindowIcon(doorstoplogo)
    splitter = CustomSplitter()

    screen_resolution = app.desktop().screenGeometry()
    screenwidth, screenheight = screen_resolution.width(), screen_resolution.height()
    width = int(screenwidth*11/16)
    height = int(screenheight*7/16)

    splitter.resize(width, height)

    splitter.setWindowTitle('doorstop-qt {}'.format(VERSION))

    databasestextfile = Path(os.getcwd(), 'doorstopqt_databases.json')
    if not os.path.isfile(databasestextfile):
        initdirectories = InitDirectoriesView(databasestextfile, stylesheetdark)
        closeprogram = initdirectories.exec()
        if closeprogram:
            sys.exit()

    mainmenu = QMenuBar()
    mainmenu.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    #optionsmenu = mainmenu.addMenu('Options')
    changestylesheetmenu = mainmenu.addMenu('Change theme')
    darktheme = changestylesheetmenu.addAction("Dark theme")
    whitetheme = changestylesheetmenu.addAction("White theme")
    darktheme.triggered.connect(splitter.setdarkstylesheet)
    whitetheme.triggered.connect(splitter.setwhiteStylesheet)

    showhidemenu = mainmenu.addMenu('Show/hide views')
    setupfolders = mainmenu.addAction('Setup folders')
    setupfolders.triggered.connect(lambda: setupdirectories(app, splitter, databasestextfile, mainmenu, showhidemenu))
    storeview = mainmenu.addAction('Store view')
    storeview.triggered.connect(lambda: storeviews(splitter))

    loadviews(app, splitter, databasestextfile, mainmenu, showhidemenu)

    sys.exit(app.exec_())


def loadviews(app, splitter, databasestextfile, mainmenu, showhidemenu):
    splitter.addWidget(mainmenu)
    databasedict = getdictfromfile(databasestextfile)
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


        for v in view.otherheaders:
            if v.capitalize() in linkviews:
                lv = linkviews[v.capitalize()][0]
                del linkviews[v.capitalize()][0]
                view.database.add_other_listeners(lv)
        try:
            view.reqtestlinkview.gotoclb = viewsdict[view.otherheaders[0].capitalize()].selectfunc
            view.reqtestlinkview2.gotoclb = viewsdict[view.otherheaders[1].capitalize()].selectfunc
        except:
            pass
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
    if 'Test' in viewsdict and 'Product' in viewsdict:
        viewsdict['Test'].itemview.applytootheritem = viewsdict['Product'].reqtestlinkview2.updatedata

    parser = ArgumentParser()
    parser.add_argument("-p", "--publish-all-tests", dest="publish", default=False,
                        help="Publish the test for all products")
    #  doorstop-qt -p True
    # to publish test for all products
    args = parser.parse_args()
    if args.publish:
        productview = viewsdict['Product']
        productview.publishalltestsforallproducts()
        sys.exit()
    #splitter.addWidget(reqview)
    #splitter.addWidget(testview)
    #splitter.addWidget(productview)

    splitter.setOrientation(Qt.Vertical)

    children = splitter.findChildren(QSplitter)
    for id, child in enumerate(children):
        loadWindowSettings(child, str(id))

    splitter.show()
    showfile = Path(os.getcwd(), 'doorstopqt_showhideviews.json')
    if os.path.isfile(showfile):
        d = getdictfromfile(showfile)
    else:
        d = {}
    for view in views:
        view.movebuttons()
        if view.header in d:
            if d[view.header] == 'hide':
                view.hide()
        inithideshow(view, showhidemenu)

if __name__ == '__main__':
    main()
