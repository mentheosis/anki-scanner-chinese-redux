from aqt import mw
from PyQt5.QtWidgets import QDialogButtonBox, QLabel, QVBoxLayout, QHBoxLayout, QButtonGroup, QFileDialog, QTextBrowser, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QRadioButton, QPlainTextEdit
from PyQt5 import QtCore, QtWidgets

from .mr_async_worker_thread import TextScannerThreadAsync
from .mr_window import MatterRabbitWindow
from .singletons import config

def showReader():
    mw.reader_worker = TextScannerThreadAsync()

    outerLayout = QVBoxLayout()
    colLayout = QHBoxLayout()
    leftLayout = QVBoxLayout()
    rightLayout = QVBoxLayout()
    outputText = QTextBrowser()

    topLabel = QLabel()
    topLabel.setWordWrap(True)
    topLabel.setText('''<div style="font-weight: bold; font-size:24px; width: 5em; text-align:center;">
        读书吧''')
    outerLayout.addWidget(topLabel)

    scanButtonLayout = QHBoxLayout()

    scanBtn = QPushButton('Parse the text')
    cancelBtn = QPushButton('Stop')
    cancelBtn.setEnabled(False)
    noteBtn = QPushButton('Update my cards')
    noteBtn.setEnabled(False)

    scanButtonLayout.addWidget(scanBtn)
    scanButtonLayout.addWidget(cancelBtn)
    scanButtonLayout.addWidget(noteBtn)

    rightLayout.addLayout(scanButtonLayout)
    rightLayout.addWidget(outputText)
    colLayout.addLayout(leftLayout)
    colLayout.addLayout(rightLayout)
    outerLayout.addLayout(colLayout)

    anki_db_path = config['textScanner']['anki_db_path']['val']

    ui_inputs = {
        'read_text': 'Text to read',
        'missed_words': 'Missed words'
    }

    controls = []
    for ipt in ui_inputs:
        label = QLabel()
        label.setWordWrap(True)
        label.setText(ui_inputs[ipt])

        if ipt == 'read_text':
            clipboard_input = QPlainTextEdit()
            label.setText("<span><b>Input text:</b></span>")
            controls.append({"key":ipt, "label":label, "input":clipboard_input})

        elif ipt == 'missed_words':
            input = QLineEdit()
            input.setText("None")
            controls.append({"key":ipt, "label":label, "input":input})

    for control in controls:
        leftLayout.addWidget(control['label'])
        leftLayout.addWidget(control['input'])
        leftLayout.addStretch()


    def gather_ui_inputs():
        inputs = {}
        for control in controls:
            if control['key'] == 'read_text':
                inputs[control['key']] = control['input'].toPlainText()
            elif control['key'] == 'missed_words':
                inputs[control['key']] = control['input'].text()
        return inputs


    def runReader():
        inputs = gather_ui_inputs();
        text = inputs['read_text']
        missedWords = inputs['missed_words']
        mw.reader_worker.runReader(text, missedWords, anki_db_path)
        cancelBtn.setEnabled(False)

    def onReaderFinished():
        noteBtn.setEnabled(True)

    def updateCards():
        mw.reader_worker.runReaderAnswerCardsSync()

    def log(message):
        outputText.append(message)

    def updateTextOutputFromThread(text):
        if mw.reader_worker.exiting == False:
            log(text)

    def onCancel():
        #resetButton()
        if hasattr(mw,'reader_worker'):
            mw.reader_worker.interrupt_and_quit = True
            mw.reader_worker.sig.emit("told worker to quit..")

    def onDialogClose():
        mw.reader_worker.exiting = True
        onCancel()

    mw.reader_worker.sig.connect(updateTextOutputFromThread)
    mw.reader_worker.finished.connect(onReaderFinished)

    scanBtn.setStyleSheet("background-color: #8DE1DD")
    scanBtn.clicked.connect(runReader)
    # if you dont initialize the stylesheet on the button it seems like things break weirdly, so just do it
    cancelBtn.setStyleSheet("color: #000")
    cancelBtn.clicked.connect(onCancel)
    # if you dont initialize the stylesheet on the button it seems like things break weirdly, so just do it
    noteBtn.setStyleSheet("color: #000")
    noteBtn.clicked.connect(updateCards)

    dialog = MatterRabbitWindow(outerLayout, onDialogClose, mw)
    dialog.resize(900,650)
    dialog.setWindowTitle('Reader Mode')
    dialog.show()
