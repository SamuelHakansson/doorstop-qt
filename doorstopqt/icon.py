from PyQt5.QtWidgets import QStyle
from PyQt5.QtWidgets import QCommonStyle
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class Icon(QIcon):
    def __init__(self):
        super(Icon, self).__init__()

        style = QCommonStyle()
        icons = [x for x in dir(QStyle) if x.startswith('SP_')]
        self.names = []
        for name in icons:
            icon = style.standardIcon(getattr(QStyle, name))
            setattr(self, name[3:], icon)
            self.names.append(name[3:])

        self.setThemeName('Papirus')

