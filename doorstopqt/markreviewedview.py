from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from doorstop.common import DoorstopError
from doorstop.core import publisher
from .icon import Icon
from pathlib import Path
import re

EXTENSIONS = (
    'markdown.extensions.extra',
    'markdown.extensions.sane_lists'
)


class MarkReviewedView(QWidget):
    def __init__(self, publishtest=False, parent=None):
        super(MarkReviewedView, self).__init__(parent)

        self.db = None
        self.currentuid = None

        grid = QHBoxLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        self.reflabel = QLabel('External ref:')
        self.refloc = QLabel('')
        self.ref = QLineEdit()
        self.reflabel.setVisible(False)
        self.ref.setVisible(False)
        self.refloc.setVisible(False)
        self.markreviewed = QPushButton('Mark as reviewed')
        self.markreviewed.setVisible(False)
        papirusicons = Icon()
        sendicon = papirusicons.fromTheme("document-send-symbolic")
        self.publish = QPushButton(sendicon, 'Publish')
        self.publish.setVisible(True)
        self.getotherdbitems = None
        self.readlinkview = None
        self.EXPECTEDRESULTS = 'expectedresults'
        self.INPUTVARIABLES = 'inputvariables'

        def ref():
            if self.currentuid is None:
                return
            data = self.db.find(self.currentuid)
            data.ref = self.ref.text()
            self.read(self.currentuid)
            self.setFocus(False)
        self.ref.editingFinished.connect(ref)
        self.ref.returnPressed.connect(ref)

        def markreviewed():
            if self.currentuid is None:
                return
            data = self.db.find(self.currentuid)
            data.review()
            data.clear()
            self.read(self.currentuid)
            if self.readlinkview:
                self.readlinkview(self.currentuid)
        self.markreviewed.clicked.connect(markreviewed)

        def publishtestforproduct():
            tree, items, selecteduid = self.getotherdbitems()
            path = tree.root
            pathtodoc = Path(path, "tests-for-"+selecteduid)
            activedict = {}
            textdict = {}
            for doc in tree.documents:
                for item in doc.items:
                    activedict[str(item)] = item.active
                    textdict[str(item)] = item.text
            product = self.db.find(self.currentuid)
            for doc in tree.documents:
                for item in doc.items:
                    if item in items:
                        newitemtext = item.text
                        item.active = True
                        if self.INPUTVARIABLES in product.data:
                            for inputvar in product.data[self.INPUTVARIABLES]:
                                varname = inputvar[0]
                                try:
                                    varvalue = inputvar[1]
                                except IndexError:
                                    varvalue = ''
                                newitemtext = re.sub(r"\b%s\b" % varname, varvalue, newitemtext)
                        else:
                            newitemtext = re.sub('', '', newitemtext)
                        if self.EXPECTEDRESULTS in product.data:
                            for pair in product.data[self.EXPECTEDRESULTS]:
                                if str(pair[0]) == str(item.uid):
                                    newitemtext = newitemtext + '\n\n Expected results: \n\n' + pair[1]
                        item.text = newitemtext
                        item.save()

                    else:
                        item.active = False
            '''
            Says in the doorstop documentation that the publish method can take a list of items. Didn't manage to get it
            to work because at a point it gets to the method 'iter_documents' which returns it wrong. The workaround is
            to add text to all chosen items and set the other to inactive. 
            //Samuel
            '''
            publisher.publish(tree, pathtodoc, extensions=EXTENSIONS)

            for doc in tree.documents:
                for item in sorted(i for i in doc._iter()):
                    if item.active:
                        item._data['text'] = textdict[str(item)]
                        item.save()
                    if str(item) in activedict:
                        item.active = activedict[str(item)]

        def publishdocs():
            publisher.publish(self.db.root, Path(self.db.root.vcs.path, "public"))
        self.publish.clicked.connect(publishdocs)

        grid.addWidget(self.reflabel)
        grid.addWidget(self.ref)
        grid.addWidget(self.refloc)
        grid.addStretch(1)
        grid.addWidget(self.markreviewed)
        if publishtest:
            self.publishtest = QPushButton(sendicon, 'Publish test for product')
            self.publishtest.setVisible(True)
            self.publishtest.clicked.connect(publishtestforproduct)
            grid.addWidget(self.publishtest)

        grid.addWidget(self.publish)
        self.setLayout(grid)

    def connectdb(self, db):
        self.db = db
        self.read(self.currentuid)

    def read(self, uid):
        if uid is None:
            return
        self.currentuid = None
        if self.db is None:
            return
        data = self.db.find(uid)
        if data is None:
            return

        self.ref.setText(data.ref)
        self.refloc.setText('')
        if data.ref != '':
            try:
                refloc = data.find_ref()
            except DoorstopError:
                self.refloc.setText('(not found)')
            else:
                if refloc[1]:
                    self.refloc.setText('{}:{}'.format(refloc[0], refloc[1]))
                else:
                    self.refloc.setText('{}'.format(refloc[0]))
        if data.reviewed and data.cleared:
            self.markreviewed.setVisible(False)
        else:
            self.markreviewed.setVisible(True)
        self.currentuid = uid

    def showref(self, b):
        if b:
            self.reflabel.setVisible(True)
            self.ref.setVisible(True)
            self.refloc.setVisible(True)
        else:
            self.reflabel.setVisible(False)
            self.ref.setVisible(False)
            self.refloc.setVisible(False)


