from PyQt5.QtWidgets import QMainWindow, QWidget

# class that we will use to generate all our UI windows
class MatterRabbitWindow(QMainWindow):
    def __init__(self, contentLayout, onCloseFn, parent=None):
        super(MatterRabbitWindow, self).__init__(parent)
        self.onCloseFn = onCloseFn
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(contentLayout)

    def closeEvent(self, evnt):
        self.onCloseFn()
