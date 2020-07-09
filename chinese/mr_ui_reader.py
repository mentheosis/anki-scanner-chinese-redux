from aqt import mw
from PyQt5.QtWidgets import QMainWindow, QDialogButtonBox, QLabel, QVBoxLayout, QHBoxLayout, QButtonGroup, QFileDialog, QTextBrowser, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QRadioButton, QPlainTextEdit
from PyQt5.QtGui import QStandardItem, QColor
from PyQt5 import QtCore, QtWidgets

from .mr_async_worker_thread import TextScannerThreadAsync
from .singletons import config
from .mr_window import MatterRabbitWindow


##########################################################
# This is the window to configure how notes will be auto-imported
##
def showReader():

    dev_mode = config.config['textScanner']['dev_mode']['val']

    outputText = QTextBrowser()
    def log(message, level=None):
        localLevel = level
        if level == None:
            localLevel = 'debug'
        if dev_mode == True or localLevel != 'debug':
            outputText.append(message)

    outerLayout = QVBoxLayout()
    colLayout = QHBoxLayout()
    leftLayout = QVBoxLayout()
    rightLayout = QVBoxLayout()

    cntTopLabel = QLabel()
    cntTopLabel.setWordWrap(True)
    cntTopLabel.setText('''<div style="font-weight: bold; font-size:24px; width: 5em; text-align:center;">
        读书吧</div>
        <div>Welcome to reader mode! Paste the text that you read, and a list of words that you had to look up, and this will update your flashcards accordingly.</div>
        <br>''')
    outerLayout.addWidget(cntTopLabel)
    #outerLayout.addStretch()


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


    def runReader():
        inputs = gather_ui_inputs();
        text = ui_inputs['read_text']
        missedWords = ui_inputs['missed_words']

        mw.reader_worker.setReaderInputs(text, missedWords)
        mw.reader_worker.setMode('reader')
        mw.reader_worker.run()

    def finishReader():
        #(learnedCount, missedCount) = mrtr.answerCards()
        #log("Learned: " + str(learnedCount) + "Missed: " + str(missedCount), 'info')
        log("Click!!")
        outputText.append("clicksfdfsd")

    def onReaderFinished():
        log("Nicerr!")
        log("Nice!", 'info')
        noteBtn.setEnabled(True)


    def updateTextOutputFromThread(text):
        if mw.reader_worker.exiting == False:
            log(text, "info")

    if not hasattr(mw, 'reader_worker'):
        mw.reader_worker = TextScannerThreadAsync()
    mw.reader_worker.sig.connect(updateTextOutputFromThread)
    mw.reader_worker.finished.connect(onReaderFinished)
    log("Welcome to the reader",'info')

    def onCancel():
        if hasattr(mw,'reader_worker'):
            mw.reader_worker.interrupt_and_quit = True
            mw.reader_worker.sig.emit("told worker to quit..")

    def onDialogClose():
        mw.reader_worker.exiting = True
        onCancel()


    scanBtn = QPushButton('Parse the text!')
    cancelBtn = QPushButton('Stop everything!')
    cancelBtn.setEnabled(False)
    noteBtn = QPushButton('Update my cards')
    #noteBtn.setEnabled(False)

    scanButtonLayout = QHBoxLayout()
    scanButtonLayout.addWidget(scanBtn)
    scanButtonLayout.addWidget(cancelBtn)
    scanButtonLayout.addWidget(noteBtn)

    scanBtn.clicked.connect(runReader)
    noteBtn.clicked.connect(finishReader)
    cancelBtn.clicked.connect(onCancel)

    rightLayout.addLayout(scanButtonLayout)
    rightLayout.addWidget(outputText)
    colLayout.addLayout(leftLayout)
    colLayout.addLayout(rightLayout)
    outerLayout.addLayout(colLayout)

    dialog = MatterRabbitWindow(outerLayout, onDialogClose, mw)
    dialog.resize(950,700)
    dialog.setWindowTitle('Chinese Text Scanner - Reader mode')
    dialog.show()
