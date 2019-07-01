#!/usr/bin/env python

import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .icon import Icon


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

        icon = Icon()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.htmlview = QTextEdit()
        self.htmlview.setReadOnly(True)
        self.editview = MarkdownEditor()
        self.editview.setWordWrapMode(QTextOption.ManualWrap)
        self.editview.setPlainText(text)
        self.previewbtn = QPushButton("Preview")
        self.previewbtn.clicked.connect(self.viewhtml)
        self.editbtn = QPushButton("Edit")
        self.editbtn.clicked.connect(self.vieweditor)
        self.discardbtn = QPushButton(icon.DialogCancelButton, "Revert")
        self.discardbtn.clicked.connect(self.discard)
        self.discardbtn.setVisible(False)
        self.savebtn = QPushButton(icon.DialogSaveButton, "Save")
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

        self.layout.addWidget(self.editview)
        self.layout.addWidget(self.htmlview)
        self.layout.addWidget(buttonrow)
        self.text = self.editview.document().toPlainText
        self.connectzoomfunctions()
        self.modeclb = None
        self.viewhtml()
        self.readfunc = None
        self.savefunc = None
        self.cache = {}
        self.currentuid = None
        self.locked = False

        def textChanged():
            if self.currentuid is not None:
                self.cache[self.currentuid]['changed'] = True
                self.savebtn.setVisible(True)
                self.discardbtn.setVisible(True)
        self.editview.textChanged.connect(textChanged)

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

    def vieweditor(self):
        self.editview.setVisible(True)
        self.previewbtn.setVisible(True)
        self.htmlview.setVisible(False)
        self.editbtn.setVisible(False)
        self.editview.setFocus()
        if self.modeclb:
            self.modeclb(True)

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

            self.savebtn.setVisible(False)
            self.discardbtn.setVisible(False)
            if uid in self.cache and 'text' in self.cache[uid]:
                text = self.cache[uid]['text']
                if self.cache[uid]['changed']:
                    self.savebtn.setVisible(True)
                    self.discardbtn.setVisible(True)
            elif self.readfunc is not None:
                self.cache[uid] = {'changed': False}
                text = self.readfunc(uid)
            else:
                uid = None
                text = ''

            self.currentuid = None
            self.editview.setPlainText(text)
            self.currentuid = uid
            self.viewhtml()

    def save(self):
        if self.savefunc is None:
            return
        if self.currentuid is None:
            return
        if self.currentuid not in self.cache:
            return
        self.savefunc(self.currentuid, self.text())
        self.cache[self.currentuid]['changed'] = False
        self.savebtn.setVisible(False)
        self.discardbtn.setVisible(False)
        if 'text' in self.cache[self.currentuid]:
            del self.cache[self.currentuid]['text']

    def discard(self):
        if self.currentuid not in self.cache:
            return
        del self.cache[self.currentuid]
        uid = self.currentuid
        self.currentuid = None
        self.read(uid)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MarkdownView()
    w.show()

    sys.exit(app.exec_())
