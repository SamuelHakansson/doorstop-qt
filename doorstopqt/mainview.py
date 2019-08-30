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
from doorstopqt.initdirectoriesview import InitDirectoriesView, DirectoryButtons
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
        self.movebuttonfuncs = []
        self.setdarkstylesheet()
        self.iconchanger = Icon()

    def resizeEvent(self, a0: QResizeEvent) -> None:
        super().resizeEvent(a0)
        self.movebuttons()

    def setwhiteStylesheet(self):
        self.setStyleSheet(stylesheetwhite)


    def setdarkstylesheet(self):
        self.setStyleSheet(stylesheetdark)

    def setdefaultstylesheet(self):
        self.setStyleSheet("")

    def movebuttons(self):
        for move in self.movebuttonfuncs:
            move()




GEOMETRY = "geometry"
WINDOWSTATE = "windowState"
DOORSTOPQT = "doorstop-qt"



def saveWindowSettings(splitter, id):
    settings = QSettings(DOORSTOPQT, id)
    settings.setValue(GEOMETRY, splitter.saveGeometry())
    settings.setValue(WINDOWSTATE, splitter.saveState())


def loadWindowSettings(splitter, id):
    settings = QSettings(DOORSTOPQT, id)
    if not settings.value(GEOMETRY):
        return
    saved_geometry = settings.value(GEOMETRY)
    splitter.restoreGeometry(saved_geometry)
    saved_state = settings.value(WINDOWSTATE)
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
    showhidefile = Path(os.getcwd(), SHOWHIDEFILE)
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


def getdictfrompath(path, names):
    if not os.path.exists(path):
        return
    databasedict = {}
    dirs = os.listdir(path)
    for name in names:
        for dir in dirs:
            if name.lower() in dir.lower():
                databasedict[name] = str(os.path.abspath(Path(path, dir)))
    return databasedict


def setupdirectories(app,  splitter, databasestextfile, mainmenu, showhidemenu, databasenames):
    initdirectories = DirectoryButtons(Icon(), databasestextfile, databasenames)
    if initdirectories.exec() is False:
        clearlayout(splitter)
        showhidemenu.clear()

        loadviews(app, splitter, databasestextfile, mainmenu, showhidemenu)


def clearlayout(splitter):
    for i in reversed(range(splitter.count())):
        splitter.widget(i).setParent(None)
    splitter.movebuttonfuncs = []


def storeviews(mainsplitter):
    splitters = mainsplitter.findChildren(QSplitter)
    for id, splitter in enumerate(splitters):
        saveWindowSettings(splitter, str(id))


def finddatabasepath(name, databasestextfile):
    if os.path.isfile(databasestextfile):
        file_obj = open(databasestextfile, 'r')
        try:
            databasedict = json.load(file_obj)
            if name in databasedict:
                return databasedict[name]
        except JSONDecodeError:
            return


DATABASESFILE = 'doorstopqt_databases.json'
SHOWHIDEFILE = 'doorstopqt_showhideviews.json'


def main():

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    parser = ArgumentParser()
    parser.add_argument("-p", "--publish-all-tests", dest="path", default=False,
                        help="Publish the test for all products")
    # doorstop-qt -p "path\to\repository"
    # to publish test for all products
    args = parser.parse_args()
    databasenames = [REQUIREMENT, TEST, PRODUCT]
    if args.path:
        databasedict = getdictfrompath(args.path, databasenames)
        if databasedict is None:
            print('Not a valid path', flush=True)
            sys.exit()
        loadviewstopublish(databasedict)
        sys.exit()


    icons = QIcon()
    icons.setThemeName('Papirus')
    doorstopicon = icons.fromTheme('ds-logo-new')
    app.setWindowIcon(doorstopicon)
    splitter = CustomSplitter()
    screen_resolution = app.desktop().screenGeometry()
    screenwidth, screenheight = screen_resolution.width(), screen_resolution.height()
    width = int(screenwidth*11/16)
    height = int(screenheight*7/16)

    splitter.resize(width, height)

    splitter.setWindowTitle('doorstop-qt {}'.format(VERSION))

    databasestextfile = Path(os.getcwd(), DATABASESFILE)

    if not os.path.isfile(databasestextfile):
        initdirectories = InitDirectoriesView(databasestextfile, databasenames, style=stylesheetdark)
        closeprogram = initdirectories.exec()
        if closeprogram:
            sys.exit()

    mainmenu = QMenuBar()
    mainmenu.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    showhidemenu = mainmenu.addMenu('Show/hide views')
    storeview = mainmenu.addAction('Store view')
    storeview.triggered.connect(lambda: storeviews(splitter))
    setupfolders = mainmenu.addAction('Select working folder')
    setupfolders.triggered.connect(lambda: setupdirectories(app, splitter, databasestextfile, mainmenu, showhidemenu, databasenames))

    changestylesheetmenu = mainmenu.addMenu('Change theme')
    darktheme = changestylesheetmenu.addAction("Dark theme")
    whitetheme = changestylesheetmenu.addAction("White theme")
    darktheme.triggered.connect(splitter.setdarkstylesheet)
    whitetheme.triggered.connect(splitter.setwhiteStylesheet)

    databasedict = getdictfromfile(databasestextfile)
    loadviews(app, splitter, databasedict, mainmenu, showhidemenu)

    sys.exit(app.exec_())


REQUIREMENT = 'Requirement'
TEST = 'Test'
PRODUCT = 'Product'


def loadviews(app, splitter, databasedict, mainmenu, showhidemenu):
    splitter.addWidget(mainmenu)

    headers = [(REQUIREMENT, ReqView), (TEST, TestView), (PRODUCT, ProductView)]

    views = []
    viewsdict = {}
    for header in headers:
        name = header[0]
        viewtype = header[1]
        if name in databasedict:
            view = viewtype()
            views.append(view)
            viewsdict[name] = view

    linkviews = {}
    for view in views:
        linkviews[view.header] = [view.linkotherview, view.linkotherview2]
    databasestextfilepath = Path(os.getcwd(), DATABASESFILE)
    for i, view in enumerate(views):
        view.tree.clipboard = lambda x: app.clipboard().setText(x)
        databasepath = finddatabasepath(view.header, databasestextfilepath)
        view.database = view.calldatabase(databasepath, databasestextfilepath, name=view.header)
        view.database.add_listeners([view.attribview, view.linkview, view.linkotherview, view.linkotherview2,
                                     view.tree, view.docview, view.itemview])
        view.docview.reloaddatabase = view.database.opennewdatabase

        for v in view.otherheaders:
            if v.capitalize() in linkviews:
                lv = linkviews[v.capitalize()][0]
                del linkviews[v.capitalize()][0]
                view.database.add_other_listeners(lv)
        try:
            view.linkotherview.gotoclb = viewsdict[view.otherheaders[0].capitalize()].selectfunc
            view.linkotherview2.gotoclb = viewsdict[view.otherheaders[1].capitalize()].selectfunc
        except:
            pass
        splitter.addWidget(view)
    if views:
        os.chdir(views[0].database.path)  # for some reason, pictures won't load without "resetting" the path
    if TEST in viewsdict and PRODUCT in viewsdict:
        viewsdict[TEST].itemview.applytootheritem = viewsdict[PRODUCT].linkotherview2.updatedata

    splitter.setOrientation(Qt.Vertical)

    children = splitter.findChildren(QSplitter)
    for id, child in enumerate(children):
        loadWindowSettings(child, str(id))

    splitter.show()
    showfile = Path(os.getcwd(), SHOWHIDEFILE)
    if os.path.isfile(showfile):
        d = getdictfromfile(showfile)
    else:
        d = {}
    for view in views:
        if view.header in d:
            if d[view.header] == 'hide':
                view.hide()
        inithideshow(view, showhidemenu)
        splitter.movebuttonfuncs.append(view.movebuttons)
        view.movebuttons()


def loadviewstopublish(databasedict):
    headers = [(REQUIREMENT, ReqView), (TEST, TestView), (PRODUCT, ProductView)]
    views = []
    viewsdict = {}
    for header in headers:
        name = header[0]
        viewtype = header[1]
        if name in databasedict:
            view = viewtype()
            views.append(view)
            viewsdict[name] = view
    if not viewsdict:
        print("{} {}{} {}{} {} {}".format('Not a path containg folders with the names:', REQUIREMENT.lower(), ',', TEST.lower(), ',', 'or', PRODUCT.lower(), 'in it'), flush=True)
        sys.exit()
    linkviews = {}
    for view in views:
        linkviews[view.header] = [view.linkotherview, view.linkotherview2]
    databasestextfilepath = Path(os.getcwd(), DATABASESFILE)
    for i, view in enumerate(views):
        try:
            databasepath = databasedict[view.header]
        except KeyError:
            print("Didn't find path for " + view.header, flush=True)
            sys.exit()

        view.database = view.calldatabase(databasepath, databasestextfilepath, name=view.header)
        view.database.add_listeners([view.attribview, view.linkview, view.linkotherview, view.linkotherview2,
                                     view.tree, view.docview, view.itemview])
        view.docview.reloaddatabase = view.database.opennewdatabase

        for v in view.otherheaders:
            if v.capitalize() in linkviews:
                lv = linkviews[v.capitalize()][0]
                del linkviews[v.capitalize()][0]
                view.database.add_other_listeners(lv)
        try:
            view.linkotherview.gotoclb = viewsdict[view.otherheaders[0].capitalize()].selectfunc
            view.linkotherview2.gotoclb = viewsdict[view.otherheaders[1].capitalize()].selectfunc
        except:
            pass

    if views:
        os.chdir(views[0].database.path)  # for some reason, pictures won't load without "resetting" the path
    if TEST in viewsdict and PRODUCT in viewsdict:
        viewsdict[TEST].itemview.applytootheritem = viewsdict[PRODUCT].linkotherview2.updatedata

    productview = viewsdict[PRODUCT]
    productview.publishalltestsforallproducts()


if __name__ == '__main__':
    main()
