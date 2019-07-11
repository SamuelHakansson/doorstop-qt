from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from .icon import Icon


class RevertButton(QPushButton):
    def __init__(self):
        super(RevertButton, self).__init__()

        papirusicons = Icon()

        reverticon = papirusicons.fromTheme("document-revert")

        self.revertbtn = QPushButton(reverticon, '')
        self.setIcon(reverticon)
        self.hide()
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setToolTip('Revert')

        op = QGraphicsOpacityEffect()
        self.setGraphicsEffect(op)
        self.fadeoutanimation = QPropertyAnimation(op, b"opacity")
        self.fadeoutanimation.setDuration(1000)
        self.fadeoutanimation.setStartValue(1)
        self.fadeoutanimation.setKeyValueAt(0.5, 0)
        self.fadeoutanimation.setEndValue(1)


    def animate(self):
        self.fadeoutanimation.start()

    def show(self) -> None:
        self.animate()
        super().show()

