###################
## UI screens
from aqt import mw
from PyQt5.QtWidgets import QDialogButtonBox, QLabel, QVBoxLayout, QHBoxLayout, QButtonGroup, QFileDialog, QTextBrowser, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QRadioButton, QPlainTextEdit
from PyQt5 import QtCore, QtWidgets

import traceback
from .mr_async_worker_thread import TextScannerThreadAsync
from .mr_window import MatterRabbitWindow
from .singletons import config

#########################################################
# This is the main text scanning and dev-mode UI window
##
def showTest():
    mw.mr_worker = TextScannerThreadAsync()

    outerLayout = QVBoxLayout()
    colLayout = QHBoxLayout()
    leftLayout = QVBoxLayout()
    rightLayout = QVBoxLayout()
    outputText = QTextBrowser()

    topLabel = QLabel()
    topLabel.setWordWrap(True)
    topLabel.setText('''TEST''')
    #label.setOpenExternalLinks(True)
    outerLayout.addWidget(topLabel)
    #outerLayout.addStretch()

    scanButtonLayout = QHBoxLayout()

    scanBtn = QPushButton('Run the scan!')
    cancelBtn = QPushButton('Stop everything!')
    cancelBtn.setEnabled(False)
    printBtn = QPushButton('Display all found')
    printBtn.setEnabled(False)
    noteBtn = QPushButton('Create anki notes')
    noteBtn.setEnabled(False)

    scanButtonLayout.addWidget(scanBtn)
    scanButtonLayout.addWidget(cancelBtn)
    scanButtonLayout.addWidget(printBtn)
    scanButtonLayout.addWidget(noteBtn)

    rightLayout.addLayout(scanButtonLayout)
    rightLayout.addWidget(outputText)
    colLayout.addLayout(leftLayout)
    colLayout.addLayout(rightLayout)
    outerLayout.addLayout(colLayout)
    #layout.addWidget(buttonBox)

    def updateTextOutput(text):
        if mw.mr_worker.exiting == False:
            outputText.append(text)

    def test():
        outputText.append("sdfsdfsdfssd!")

    def onCancel():
        resetButton()
        if hasattr(mw,'mr_worker'):
            mw.mr_worker.interrupt_and_quit = True
            mw.mr_worker.sig.emit("told worker to quit..")

    def onDialogClose():
        mw.mr_worker.exiting = True
        onCancel()

    #scanBtn.clicked.connect(runScanner)
    scanBtn.clicked.connect(test)
    scanBtn.setStyleSheet("background-color: #8DE1DD")

    dialog = MatterRabbitWindow(outerLayout, onDialogClose, mw)
    dialog.resize(900,650)
    dialog.setWindowTitle('Chinese Text Scanner')
    dialog.show()
