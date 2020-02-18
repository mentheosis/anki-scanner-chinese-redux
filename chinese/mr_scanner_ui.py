###################
## UI screens
import time
from aqt import mw
from aqt.utils import askUser, showInfo
from anki.find import Finder

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QHBoxLayout, QFileDialog, QTextBrowser, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QRadioButton, QPlainTextEdit
from PyQt5 import QtCore, QtWidgets

from os.path import dirname, join, realpath

from .singletons import config
from .database import Dictionary
from .mr_text_scanner import TextScanner
from .mr_note_maker import NoteMaker


class TextScannerThreadAsync(QtCore.QThread):
    sig = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # internal default params
        self.interrupt_and_quit = False
        self.run_mode = "scan"

    def refresh_inputs(self,
    anki_db_path,
    anki_db_field_indices,
    anki_tags_to_exclude,
    include_sound,
    media_dir_path,
    file_or_dir,
    file_to_scan,
    tag_for_new_cards,
    output_path,
    input_encoding,
    scan_mode):
        self.anki_db_path = anki_db_path
        self.anki_db_field_indices = anki_db_field_indices
        self.anki_tags_to_exclude = anki_tags_to_exclude
        self.include_sound = include_sound
        self.media_dir_path = media_dir_path
        self.file_or_dir = file_or_dir
        self.file_to_scan = file_to_scan
        self.tag_for_new_cards = tag_for_new_cards
        self.output_path = output_path
        self.input_encoding = input_encoding
        self.scan_mode = scan_mode

    def setMode(self,mode):
        self.interrupt_and_quit = False
        self.run_mode = mode

    def run(self):
        if self.run_mode == 'scan':
            dictionary = Dictionary()
            # worker thread needs its own dictionry, so cant use singleton here
            joined_db_path = join(dirname(realpath(__file__)),self.anki_db_path)
            sc = TextScanner(dictionary, joined_db_path, self.anki_db_field_indices, self.anki_tags_to_exclude, self.sig, self)
            self.new_char_words, self.new_words, self.new_chars = sc.scan_and_print(self.file_to_scan, self.file_or_dir, self.input_encoding, self.scan_mode)
            dictionary.conn.close()

        elif self.run_mode == 'print':
            to_print={}
            if self.scan_mode == "new_words":
                to_print = self.new_words
            elif self.scan_mode == "new_chars":
                to_print = self.new_chars
            else:
                to_print = self.new_char_words
            i = 1
            for note in to_print:
                item = to_print[note]
                self.sig.emit(f"\nSimplified: {item.simplified}, Traditional: {item.traditional}, Pinyin: {item.pinyin}\nDefinition: {item.definition}\nIndex: {i}, First appearance: {item.sort_order}, Count: {item.count}\nSentence: {item.sentence}")
                i += 1

        elif self.run_mode == 'make_notes':
            dictionary = Dictionary()
            nm = NoteMaker(dictionary, self.media_dir_path, self.sig, self)

            if self.include_sound == 'true' or self.include_sound == 'True':
                include_sound = True
            else:
                include_sound = False

            if self.scan_mode == "new_words":
                new_notes = self.new_words
            elif self.scan_mode == "new_chars":
                new_notes = self.new_chars
            else:
                new_notes = self.new_char_words

            self.sig.emit(f"\nPreparing to make {len(new_notes)} new notes")
            nm.make_notes(new_notes, self.tag_for_new_cards, self.output_path, self.tag_for_new_cards, include_sound)

            if self.interrupt_and_quit == False:
                self.sig.emit("\nThanks for using the scanner! You can now import your apkg file to anki.")
            else:
                self.sig.emit("\nExiting early, no package made, thanks for using the scanner!")
            dictionary.conn.close()

        else:
            self.sig.emit(f"Worker thread has nothing to do for mode {self.run_mode}...")

def gatherControls(config, ui_mode="file"):
    config_inputs = {
        'anki_db_path':'',
        'anki_db_field_indices':'',
        'media_dir_path':'',
        'file_or_dir':'',
        'input_encoding':''
    }

    ui_inputs = {
        'file_to_scan':'''<span><b>File to scan:</b><br>This is the input file which
                will be scanned for new words. Note, it is possible to scan
                a whole collection of files at once by changing the file_or_dir
                property in the config to dir, and then putting the dir path here.</span>''',
        'scan_mode':'''<br><span><b>Mode:</b><br>Choose whether to produce a card for every new words, every new inidividual character, or only new words using new characters</span>''',
        'output_path':'''<br><span><b>Output path:</b><br>Where the resulting .apk file should be placed
                (including the filename.apk)</span>''',
        'tag_for_new_cards':'''<br><span><b>Imported deck/tag name:</b><br>This string cannot contain
                spaces. It will be applied to all new notes as a tag,
                and will also be the name of the deck imported.</span>''',
        'anki_tags_to_exclude':'''<br><span><b>Tags to exclude:</b><br>
                A comma separated list of tags, these will be excluded from
                the de-duping process. That means the scanner will still
                consider a word to be new, even if it contains a character
                in one of your existing notes tagged with one of these tags</span>''',
        'include_sound':'''<br><span><b>Include sound files:</b><br>If this is true, the scanner will
                download sound files of the word readings and include them as media in the generated notes.</span>'''
    }

    hidden_cfg = {}
    for item in config_inputs:
        if item == 'file_or_dir' and ui_mode == 'clipboard':
            hidden_cfg[item] = 'clipboard'
        else:
            hidden_cfg[item] = config['textScanner'][item]['val']

    new_words = "All new words"
    new_chars = "Individual new characters"
    new_char_words = "Only words using new chars"
    def interpretRadioBtn(b,input):
        input['mode'] = b.mode

    controls = []
    for ipt in ui_inputs:
        label = QLabel()
        label.setWordWrap(True)
        label.setText(ui_inputs[ipt])
        tryConfig = config['textScanner'].get(ipt)
        default = tryConfig['val'] if tryConfig != None else "Uninitialized"
        if ipt == 'scan_mode':
            b1 = QRadioButton(new_char_words)
            b1.mode = 'new_char_words'
            b2 = QRadioButton(new_chars)
            b2.mode = 'new_chars'
            b3 = QRadioButton(new_words)
            b3.mode = 'new_words'

            if default == 'new_char_words':
                b1.setChecked(True)
            if default == 'new_chars':
                b2.setChecked(True)
            if default == 'new_words':
                b3.setChecked(True)

            radioLayout = QHBoxLayout()
            radioLayout.addWidget(b1)
            radioLayout.addWidget(b2)
            radioLayout.addWidget(b3)

            scan_input = {"mode":default,"layout":radioLayout}
            b1.toggled.connect(lambda:interpretRadioBtn(b1, scan_input))
            b2.toggled.connect(lambda:interpretRadioBtn(b2, scan_input))
            b3.toggled.connect(lambda:interpretRadioBtn(b3, scan_input))
            controls.append({"key":ipt, "label":label, "input":scan_input})
        elif ipt == 'file_to_scan' and ui_mode == 'clipboard':
            clipboard_input = QPlainTextEdit()
            label.setText("<span><b>Input text:</b></span>")
            controls.append({"key":ipt, "label":label, "input":clipboard_input})
        else:
            input = QLineEdit()
            input.setText(default)
            controls.append({"key":ipt, "label":label, "input":input})

    return controls, hidden_cfg


class ScanDialog(QDialog):
    def __init__(self, onCloseFn, parent=None):
        super(ScanDialog, self).__init__(parent)
        self.onCloseFn = onCloseFn

    def closeEvent(self, evnt):
        self.onCloseFn()

def showTextScanner(ui_mode="file"):
    outerLayout = QVBoxLayout()
    colLayout = QHBoxLayout()
    leftLayout = QVBoxLayout()
    rightLayout = QVBoxLayout()
    outputText = QTextBrowser()

    topLabel = QLabel()
    topLabel.setWordWrap(True)
    topLabel.setText('''<div style="font-weight: bold; font-size:24px; width: 5em; text-align:center;">
        Welcome to the Chinese Text Scanner!
        <br> 大家好，这是兔子先生的魔法扫描字器！
        </div><span>This will scan a text file, find any chinese words that contain
        new characters not already in the provided anki collection, and then produce
        an .apkg file which can be imported into anki. The import file will contain
        notes for all the new words, including tone colors and audio files powered
        by the chinese-support-redux project. Additional options are available in the config file.</span><br>''')
    #label.setOpenExternalLinks(True)
    outerLayout.addWidget(topLabel)
    #outerLayout.addStretch()

    # to avoid late binding: https://stackoverflow.com/questions/3431676/creating-functions-in-a-loop
    def make_getFile(textInputObj):
        def f():
            filePath = QFileDialog.getOpenFileName(caption='Open file')[0]
            if filePath != None and filePath != '':
                textInputObj.setText(filePath)
        return f

    def make_saveFile(textInputObj):
        def f():
            filePath = QFileDialog.getSaveFileName(caption='Save file', filter="Anki package (*.apkg)", initialFilter="import_this.apkg")[0]
            if filePath != None and filePath != '':
                textInputObj.setText(filePath)
        return f

    controls, hidden_cfg = gatherControls(config, ui_mode)
    for control in controls:
        leftLayout.addWidget(control['label'])
        if control['key'] == 'scan_mode':
            leftLayout.addLayout(control['input']['layout'])
        elif control['key'] == 'file_to_scan' and ui_mode == 'file':
            fb = QPushButton("Browse files")
            fb.clicked.connect(make_getFile(control['input']))
            fileSelectL = QHBoxLayout()
            fileSelectL.addWidget(fb)
            fileSelectL.addWidget(control['input'])
            leftLayout.addLayout(fileSelectL)
        elif control['key'] == 'output_path':
            fb = QPushButton("Save to..")
            fb.clicked.connect(make_saveFile(control['input']))
            fileSelectL = QHBoxLayout()
            fileSelectL.addWidget(fb)
            fileSelectL.addWidget(control['input'])
            leftLayout.addLayout(fileSelectL)
        else:
            leftLayout.addWidget(control['input'])
        leftLayout.addStretch()

    scanBtn = QPushButton('Run the scan!')
    cancelBtn = QPushButton('Stop everything!')
    cancelBtn.setEnabled(False)
    printBtn = QPushButton('Display all found')
    printBtn.setEnabled(False)
    noteBtn = QPushButton('Create anki notes')
    noteBtn.setEnabled(False)

    scanButtonLayout = QHBoxLayout()
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


    mw.exiting = False
    def updateTextOutput(text):
        if mw.exiting == False:
            outputText.append(text)

    def resetButton():
        if mw.exiting == False:
            scanBtn.setEnabled(True)
            cancelBtn.setEnabled(False)
            if hasattr(mw.worker,'new_chars'):
                printBtn.setEnabled(True)
                noteBtn.setEnabled(True)

    def gather_ui_inputs():
        ui_inputs = {}
        for control in controls:
            if control['key'] == "scan_mode":
                ui_inputs[control['key']] = control['input']["mode"]
                config.config['textScanner'][control['key']]['val'] = control['input']['mode']
            elif control['key'] == 'file_to_scan' and ui_mode == 'clipboard':
                # dont save user input as config in this case
                ui_inputs[control['key']] = control['input'].toPlainText()
            else:
                ui_inputs[control['key']] = control['input'].text()
                config.config['textScanner'][control['key']]['val'] = control['input'].text()
        # save user choices as their config for next time.
        config.save()
        ui_inputs['anki_tags_to_exclude'] = ui_inputs['anki_tags_to_exclude'].replace(" ","")
        return ui_inputs

    mw.worker = TextScannerThreadAsync()
    mw.worker.sig.connect(updateTextOutput)
    mw.worker.finished.connect(resetButton)

    def runScanner():
        outputText.setText("Starting scan...")
        cancelBtn.setEnabled(True)
        printBtn.setEnabled(False)
        noteBtn.setEnabled(False)
        scanBtn.setEnabled(False)

        ui_inputs = gather_ui_inputs()

        mw.worker.refresh_inputs(
            hidden_cfg['anki_db_path'],
            hidden_cfg['anki_db_field_indices'],
            ui_inputs['anki_tags_to_exclude'].split(','),
            str(ui_inputs['include_sound']),
            hidden_cfg['media_dir_path'],
            hidden_cfg['file_or_dir'],
            ui_inputs['file_to_scan'],
            ui_inputs['tag_for_new_cards'],
            ui_inputs['output_path'],
            hidden_cfg['input_encoding'],
            ui_inputs['scan_mode'])
        mw.worker.setMode('scan')
        mw.worker.start()

    def printWords():
        cancelBtn.setEnabled(True)
        printBtn.setEnabled(False)
        noteBtn.setEnabled(False)
        scanBtn.setEnabled(False)

        ui_inputs = gather_ui_inputs()

        mw.worker.refresh_inputs(hidden_cfg['anki_db_path'],
            hidden_cfg['anki_db_field_indices'],
            ui_inputs['anki_tags_to_exclude'].split(','),
            str(ui_inputs['include_sound']),
            hidden_cfg['media_dir_path'],
            hidden_cfg['file_or_dir'],
            ui_inputs['file_to_scan'],
            ui_inputs['tag_for_new_cards'],
            ui_inputs['output_path'],
            hidden_cfg['input_encoding'],
            ui_inputs['scan_mode'])

        if ui_inputs['scan_mode'] == "new_chars":
            outputText.setText("Displaying characters ready for note creation")
        else:
            outputText.setText("Displaying words ready for note creation")

        mw.worker.setMode('print')
        mw.worker.start()

    def makeNotes():
        outputText.setText("")
        cancelBtn.setEnabled(True)
        printBtn.setEnabled(False)
        noteBtn.setEnabled(False)
        scanBtn.setEnabled(False)

        ui_inputs = gather_ui_inputs()

        mw.worker.refresh_inputs(hidden_cfg['anki_db_path'],
            hidden_cfg['anki_db_field_indices'],
            ui_inputs['anki_tags_to_exclude'].split(','),
            str(ui_inputs['include_sound']),
            hidden_cfg['media_dir_path'],
            hidden_cfg['file_or_dir'],
            ui_inputs['file_to_scan'],
            ui_inputs['tag_for_new_cards'],
            ui_inputs['output_path'],
            hidden_cfg['input_encoding'],
            ui_inputs['scan_mode'])

        mw.worker.setMode('make_notes')
        mw.worker.start()

    def onCancel():
        resetButton()
        if hasattr(mw,'worker'):
            mw.worker.interrupt_and_quit = True
            mw.worker.sig.emit("told worker to quit..")

    def onDialogClose():
        mw.exiting = True
        onCancel()

    scanBtn.clicked.connect(runScanner)
    printBtn.clicked.connect(printWords)
    noteBtn.clicked.connect(makeNotes)
    cancelBtn.clicked.connect(onCancel)

    dialog = ScanDialog(onDialogClose, mw)
    dialog.resize(900,800)
    scanBtn.setStyleSheet("background-color: #8DE1DD")
    #dialog.setStyleSheet("background-color: #CCCCCC")
    dialog.setWindowTitle('Chinese Text Scanner')
    dialog.setLayout(outerLayout)
    dialog.exec_()
