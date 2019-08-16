#!/usr/bin/env python

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from doorstopqt.version import VERSION
from doorstopqt.fullview import ReqView, TestView, ProductView
import resources  # resources fetches icons (don't remove)
from pathlib import Path
from doorstopqt.stylesheet import stylesheet


class CustomSplitter(QSplitter):
    """
    Custom splitter to be able to move buttons when resizing the window.
    """
    def __init__(self):
        super(CustomSplitter, self).__init__()
        self.movebuttons = None
        self.setStyleSheet(stylesheet)


    def resizeEvent(self, a0: QResizeEvent) -> None:
        if self.movebuttons:
            self.movebuttons()
        super().resizeEvent(a0)


def main():
    import sys
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    splitter = CustomSplitter()

    screen_resolution = app.desktop().screenGeometry()
    screenwidth, screenheight = screen_resolution.width(), screen_resolution.height()
    width = int(screenwidth*12/16)
    height = int(screenheight*12/16)

    splitter.resize(width, height)

    splitter.setWindowTitle('doorstop-qt {}'.format(VERSION))

    reqview = ReqView()
    testview = TestView()
    productview = ProductView()

    views = [reqview, testview, productview]
    for view in views:
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

    reqview.database.add_other_listeners([testview.reqtestlinkview, productview.reqtestlinkview])
    testview.database.add_other_listeners([reqview.reqtestlinkview, productview.reqtestlinkview2])
    productview.database.add_other_listeners([reqview.reqtestlinkview2, testview.reqtestlinkview2])

    reqview.reqtestlinkview.gotoclb = testview.selectfunc
    testview.reqtestlinkview.gotoclb = reqview.selectfunc
    productview.reqtestlinkview.gotoclb = reqview.selectfunc

    reqview.reqtestlinkview2.gotoclb = productview.selectfunc
    testview.reqtestlinkview2.gotoclb = productview.selectfunc
    productview.reqtestlinkview2.gotoclb = testview.selectfunc

    testview.itemview.applytootheritem = productview.reqtestlinkview2.updatedata

    splitter.addWidget(reqview)
    splitter.addWidget(testview)
    splitter.addWidget(productview)

    splitter.setOrientation(Qt.Vertical)
    splitter.setStretchFactor(0, 2)

    splitter.show()
    for view in views:
        view.movebuttons()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()