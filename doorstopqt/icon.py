from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class Icon(QIcon):
    def __init__(self, color=Qt.white):
        super(Icon, self).__init__()
        self.defaultcolor = color
        style = QCommonStyle()
        icons = [x for x in dir(QStyle) if x.startswith('SP_')]
        self.names = []
        for name in icons:
            icon = style.standardIcon(getattr(QStyle, name))
            setattr(self, name[3:], icon)
            self.names.append(name[3:])

        self.setThemeName('Papirus')
        self.protectedicons = ["media-floppy"]


    def colorize(self, pixmap):

        color = QColor(self.defaultcolor)  # sets color of icons
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)

        painter.fillRect(pixmap.rect(), color)

        icon = QIcon(pixmap)
        return icon

    def getpixmap(self, icon):
        if len(icon.availableSizes()) > 0:
            iconsize = icon.availableSizes()[0]
            pixmap = icon.pixmap(iconsize)
            return pixmap

    def fromTheme(self, name: str) -> 'QIcon':
        icon = super(Icon, self).fromTheme(name)
        pixmap = self.getpixmap(icon)
        if name not in self.protectedicons and pixmap is not None:
            coloredicon = self.colorize(pixmap)
        else:
            return icon
        return coloredicon
