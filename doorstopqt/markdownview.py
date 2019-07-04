#!/usr/bin/env python

import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .icon import Icon
import datetime


class SimpleMarkdownHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        import re

        self.matchAndApply('^#.*', text, 'b', sz=3)
        self.matchAndApply('^##.*', text, 'b', sz=2)
        self.matchAndApply('^###.*', text, 'b', sz=1)
        self.matchAndApply('^####.*', text, 'b', sz=0)
        self.matchAndApply('^#####.*', text, 'b', sz=-1)
        self.matchAndApply('!\[[^]]*\]\([^)]*\)', text, 'i', color=QColor('#336699'))
        self.matchAndApply('(?<!!)\[[^]]*\]\([^)]*\)', text, 'u', color=QColor('blue'))
        self.matchAndApply('(?<![\w\\\\])_((?!_\s).)*_(?!\w)', text, 'i')
        self.matchAndApply('(?<!\\\\)\*[^\s][^\*]*\*(?!\*)', text, 'i')
        self.matchAndApply('(?<!\\\\)\*\*[^\s]((?!\*\*).)*(?!\s)\*\*', text, 'b')

    def setformat(self, idx, length, attr, color=None, sz=None):
        fmt = self.format(idx)
        if 'b' in attr:
            fmt.setFontWeight(QFont.Bold)
        if 'u' in attr:
            fmt.setFontUnderline(True)
        if color is not None:
            fmt.setForeground(color)
        if 'i' in attr:
            fmt.setFontItalic(True)
        if sz is not None:
            fmt.setProperty(QTextFormat.FontSizeAdjustment, sz)

        self.setFormat(idx, length, fmt)

    def matchAndApply(self, rexp, text, attr, color=None, sz=None):
        import re

        for match in re.finditer(rexp, text):
            idx, end = match.span()
            self.setformat(idx, end - idx, attr, color, sz)


class MarkdownEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super(MarkdownEditor, self).__init__(parent)
        self.highlighter = SimpleMarkdownHighlighter(self.document())

    def dropEvent(self, ev):
        from os.path import basename
        from urllib.request import FancyURLopener
        from base64 import b64encode
        import imghdr

        c = self.cursorForPosition(ev.pos())
        s = ev.mimeData().text().split('\n')
        for url in s:
            url = url.strip()
            if len(url):
                data = FancyURLopener().open(url).read()
                t = imghdr.what(None, h=data)
                data = b64encode(data).decode('utf-8')
                if t is None:
                    continue
                if c.block().length() != 1:
                    c.insertBlock()
                if c.block().previous().length() != 1:
                    c.insertBlock()
                data = 'data:image/' + t + ';base64,' + data
                c.insertText('![{0}]({1})'.format(basename(url), data))
                if c.block().next().length() != 1:
                    c.insertBlock()
                else:
                    c.movePosition(QTextCursor.NextBlock)

        self.setTextCursor(c)

        mimeData = QMimeData()
        mimeData.setText("")
        dummyEvent = QDropEvent(ev.posF(), ev.possibleActions(),
                mimeData, ev.mouseButtons(), ev.keyboardModifiers())

        super(MarkdownEditor, self).dropEvent(dummyEvent)


class MarkdownView(QWidget):
    def __init__(self, text='', parent=None):
        super(MarkdownView, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.htmlview = QTextEdit()
        self.htmlview.selectionChanged.connect(self.vieweditor)

        self.editview = MarkdownEditor()
        self.editview.setWordWrapMode(QTextOption.ManualWrap)
        self.editview.setPlainText(text)

        self.infoview = QTextEdit()
        self.infoview.selectionChanged.connect(self.vieweditor)

        papirusicons = QIcon()
        papirusicons.setThemeName('Papirus')
        reverticon = papirusicons.fromTheme("document-revert")
        saveicon = papirusicons.fromTheme("media-floppy")
        previewicon = papirusicons.fromTheme("document-preview")
        editicon = papirusicons.fromTheme("edit")

        self.previewbtn = QPushButton(previewicon, "Preview")
        self.previewbtn.clicked.connect(self.viewhtml)
        self.editbtn = QPushButton(editicon, "Edit")
        self.editbtn.clicked.connect(self.vieweditor)
        self.discardbtn = QPushButton(reverticon, "Revert")
        self.discardbtn.clicked.connect(self.discard)
        self.discardbtn.setVisible(False)
        self.savebtn = QPushButton(saveicon, "Save")
        self.savebtn.clicked.connect(self.save)
        self.savebtn.setVisible(False)
        discardbtnsize = self.discardbtn.minimumSizeHint()
        savebtnsize = self.savebtn.minimumSizeHint()
        if discardbtnsize.width() > savebtnsize.width():
            self.discardbtn.setFixedSize(discardbtnsize)
            self.savebtn.setFixedSize(discardbtnsize)
        else:
            self.discardbtn.setFixedSize(savebtnsize)
            self.savebtn.setFixedSize(savebtnsize)

        saveshortcut = QShortcut(QKeySequence("Ctrl+S"), self.editview)
        saveshortcut.activated.connect(lambda: self.save())
        saveshortcut = QShortcut(QKeySequence("Ctrl+S"), self.htmlview)
        saveshortcut.activated.connect(lambda: self.save())

        buttongrid = QHBoxLayout()
        buttongrid.setContentsMargins(0, 0, 0, 0)
        buttongrid.addWidget(self.editbtn)
        buttongrid.addWidget(self.previewbtn)
        buttongrid.addWidget(self.discardbtn)
        buttongrid.addWidget(self.savebtn)
        buttonrow = QWidget()
        buttonrow.setLayout(buttongrid)


        textviewweight = 30
        self.layout.addWidget(self.editview, textviewweight)
        self.layout.addWidget(self.htmlview, textviewweight)
        self.layout.addWidget(QLabel('Decision log'))
        self.layout.addWidget(self.infoview, 10)

        self.decisiontakerslabeltext = 'Decision takers'
        self.decisiontakerslabelhelp = ' (separate names with comma , )'
        self.decisiontakerslabel = QLabel(self.decisiontakerslabeltext)
        self.decisiontakersline = QTextEdit()
        self.decisiontakersline.selectionChanged.connect(self.vieweditor)
        self.layout.addWidget(self.decisiontakerslabel)
        self.layout.addWidget(self.decisiontakersline, 1)

        self.lastupdatedtext = QLabel()
        self.layout.addWidget(self.lastupdatedtext)
        self.layout.addWidget(buttonrow)
        self.text = self.editview.document().toPlainText
        self.decisionlog = self.infoview.document().toPlainText
        self.decisiontakers = self.decisiontakersline.document().toPlainText
        self.connectzoomfunctions()
        self.modeclb = None
        self.viewhtml()
        self.readfunc = None
        self.itemfunc = None
        self.cache = {}
        self.currentuid = None
        self.locked = False
        self.fields = ['text', 'decisionlog', 'decisiontakers']

        def textChanged():
            if self.currentuid is not None:
                self.cache[self.currentuid]['changed'] = True
                self.savebtn.setVisible(True)
                self.discardbtn.setVisible(True)
        self.editview.textChanged.connect(textChanged)
        self.infoview.textChanged.connect(textChanged)
        self.decisiontakersline.textChanged.connect(textChanged)

    def viewhtml(self):
        from markdown import markdown
        ext = (
            'markdown.extensions.extra',
            'markdown.extensions.sane_lists'
        )

        html = markdown(self.text(), extensions=ext)
        self.htmlview.setHtml(html)
        self.htmlview.setVisible(True)
        self.editbtn.setVisible(True)
        self.editview.setVisible(False)
        self.previewbtn.setVisible(False)
        if self.modeclb:
            self.modeclb(False)
        self.decisiontakerslabel.setText(self.decisiontakerslabeltext)

    def vieweditor(self):
        self.editview.setVisible(True)
        self.previewbtn.setVisible(True)
        self.htmlview.setVisible(False)
        self.editbtn.setVisible(False)
        if self.modeclb:
            self.modeclb(True)
        self.decisiontakerslabel.setText(self.decisiontakerslabeltext + self.decisiontakerslabelhelp)

    def connectzoomfunctions(self):
        def zoomeditor(ev):
            if ev.modifiers() & Qt.ControlModifier:
                # zoom only works in read-only mode
                self.editview.setReadOnly(True)
                super(MarkdownEditor, self.editview).wheelEvent(ev)
                self.editview.setReadOnly(False)

                if self.editview.isVisible():
                    self.htmlview.wheelEvent(ev)
            else:
                super(MarkdownEditor, self.editview).wheelEvent(ev)

        htmlzoom = self.htmlview.wheelEvent
        def zoomhtml(ev):
            htmlzoom(ev)
            if self.htmlview.isVisible():
                self.editview.wheelEvent(ev)

        self.htmlview.wheelEvent = zoomhtml
        self.editview.wheelEvent = zoomeditor

    def read(self, uid):
        if not self.locked:
            if self.currentuid is not None:
                if self.currentuid in self.cache \
                        and self.cache[self.currentuid]['changed']:
                    self.cache[self.currentuid]['text'] = self.text()
                    self.cache[self.currentuid]['decisionlog'] = self.decisionlog()
                    self.cache[self.currentuid]['decisiontakers'] = self.decisiontakers()


            self.savebtn.setVisible(False)
            self.discardbtn.setVisible(False)

            if uid in self.cache and 'text' in self.cache[uid]:
                    text = self.cache[uid]['text']
            else:
                text = self.getiteminfo(uid, 'text')

            if uid in self.cache and 'decisionlog' in self.cache[uid]:
                decisionlog = self.cache[uid]['decisionlog']
            else:
                decisionlog = self.getiteminfo(uid, 'decisionlog')

            if uid in self.cache and 'decisiontakers' in self.cache[uid]:
                decisiontakers = self.cache[uid]['decisiontakers']
            else:
                decisiontakers = self.getiteminfo(uid, 'decisiontakers')

            if uid in self.cache:
                if self.cache[uid]['changed']:
                    self.savebtn.setVisible(True)
                    self.discardbtn.setVisible(True)
            else:
                self.cache[uid] = {'changed': False}

            self.currentuid = None

            self.editview.setPlainText(text)
            self.infoview.setPlainText(decisionlog)
            self.settextdecisiontakers(decisiontakers)
            lastupdated = self.getiteminfo(uid, 'lastupdated')
            if lastupdated is None:
                lastupdated = ''
            self.lastupdatedtext.setText('Last updated:' + lastupdated)


            self.currentuid = uid
            self.viewhtml()


    def save(self):
        if self.currentuid is None:
            return
        if self.currentuid not in self.cache:
            return
        self.savefunc(self.currentuid)
        self.cache[self.currentuid]['changed'] = False

        for field in self.fields:
            if field in self.cache[self.currentuid]:
                del self.cache[self.currentuid][field]
        self.updateinfo(self.currentuid)
        self.savebtn.setVisible(False)
        self.discardbtn.setVisible(False)

    def discard(self):
        if self.currentuid not in self.cache:
            return
        del self.cache[self.currentuid]
        uid = self.currentuid
        self.currentuid = None
        self.read(uid)

    def updateinfo(self, uid):
        item = self.itemfunc(uid)
        self.updatelastupdated(item)
        self.updatedecisiontakers(item)
        self.updatedecisionlog(item)

    def updatelastupdated(self, item):
        try:
            lastupdated = item._data['lastupdated']
        except KeyError:
            lastupdated = ''
        self.lastupdatedtext.setText('Last updated:'+lastupdated)

    def updatedecisiontakers(self, item):
        try:
            decisiontakers = item._data['decisiontakers']
        except KeyError:
            decisiontakers = ''
        self.settextdecisiontakers(decisiontakers)

    def updatedecisionlog(self, item):
        try:
            decisionlog = item._data['decisionlog']
        except:
            decisionlog = ''
        self.infoview.setText(decisionlog)

    def settextdecisiontakers(self, decisiontakers):
        if type(decisiontakers) is list:
            decisiontakers = ', '.join(decisiontakers)
        self.decisiontakersline.setText(decisiontakers)


    def savefunc(self, uid):
        text = self.text()
        item = self.itemfunc(uid)
        item.text = text
        decisionlog = self.decisionlog()
        decisiontakers = self.decisiontakers()

        decisiontakerstrimmed = decisiontakers.split(',')
        decisiontakerslist = []
        for name in decisiontakerstrimmed:
            if name != '' and name[0].isspace():
                name = name[1:]
            decisiontakerslist.append(name)

        currenttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        item.set('lastupdated', currenttime)
        item.set('decisionlog', decisionlog)
        item.set('decisiontakers', decisiontakerslist)
        item.save()


    def getiteminfo(self, uid, key):
        item = self.itemfunc(uid)
        try:
            decisionlog = item._data[key]
            return decisionlog
        except KeyError:
            return

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MarkdownView()
    w.show()

    sys.exit(app.exec_())
