#!/usr/bin/env python

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .fullview import ReqView, TestView, ProductView
from .version import VERSION
import resources  # resources fetches icons


class CustomSplitter(QSplitter):
    def __init__(self):
        super(CustomSplitter, self).__init__()
        self.movebuttons = None

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
    width = int(screenwidth*13/16)
    height = int(screenheight*13/16)
    splitter.resize(width, height)

    splitter.setWindowTitle('doorstop-qt {}'.format(VERSION))

    reqview = ReqView()
    testview = TestView()
    productview = ProductView()
    views = [testview, reqview, productview]
    for view in views:
        view.tree.clipboard = lambda x: app.clipboard().setText(x)

        has_started = False
        while not has_started:
            try:
                view.database = view.calldatabase()
                has_started = True
            except:
                import os
                f = str(QFileDialog.getExistingDirectory(None, "Select Directory"))
                if not os.path.isdir(f):
                    f = os.path.dirname(f)
                os.chdir(f)
        view.database.add_listeners([view.attribview, view.linkview, view.reqtestlinkview, view.tree, view.docview,
                                     view.itemview])

        def modeclb(editmode):
            if editmode:
                view.attribview.showref(True)
            else:
                view.attribview.showref(False)
        view.markdownview.modeclb = modeclb

    reqview.reqtestlinkview.setotherdb(testview.database)
    testview.reqtestlinkview.setotherdb(reqview.database)

    reqview.reqtestlinkview.gotoclb = testview.selectfunc
    testview.reqtestlinkview.gotoclb = reqview.selectfunc

    splitter.addWidget(reqview)
    splitter.addWidget(testview)  # added reversed because of problem with db and current dir
    splitter.addWidget(productview)

    splitter.setOrientation(Qt.Vertical)
    splitter.setStretchFactor(0, 2)
    splitter.show()
    for view in views:
        view.movebuttons()

    sys.exit(app.exec_())
