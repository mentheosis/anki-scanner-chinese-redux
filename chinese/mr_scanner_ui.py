###################
## UI screens
import time
from aqt import mw
from aqt.utils import askUser, showInfo
from anki.find import Finder

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout
from PyQt5.QtWidgets import QTextBrowser, QWidget, QPushButton, QAction, QLineEdit, QMessageBox
from PyQt5 import QtCore, QtWidgets

from os.path import dirname, join, realpath

from .singletons import config
from .database import Dictionary
from .mr_text_scanner import TextScanner
from .mr_note_maker import NoteMaker


def orchestrateTextScanner(
    anki_db_path,
    anki_db_field_indices,
    anki_tags_to_exclude,
    include_sound,
    media_dir_path,
    file_or_dir,
    file_to_scan,
    tag_for_new_cards,
    output_path,
    emitter):

    # worker thread needs its own dictionry, so cant use singleton here
    dictionary = Dictionary()
    joined_db_path = join(dirname(realpath(__file__)),anki_db_path)
    sc = TextScanner(dictionary, joined_db_path, anki_db_field_indices, anki_tags_to_exclude, emitter)
    nm = NoteMaker(dictionary, media_dir_path, emitter)

    new_char_words, new_words, new_chars = sc.scan_and_print(file_to_scan, file_or_dir)
    emitter.emit(f"\nPreparing to make {len(new_char_words)} new notes")
    if include_sound == 'true' or include_sound == 'True':
        include_sound = True
    nm.make_notes(new_char_words, tag_for_new_cards, output_path, tag_for_new_cards, include_sound)
    dictionary.conn.close()
    emitter.emit("\nThanks for using the scanner! You can now import your apkg file to anki.")
    return "done"


class TextScannerThreadAsync(QtCore.QThread):
    sig = QtCore.pyqtSignal(str)

    def __init__(self,
    anki_db_path,
    anki_db_field_indices,
    anki_tags_to_exclude,
    include_sound,
    media_dir_path,
    file_or_dir,
    file_to_scan,
    tag_for_new_cards,
    output_path):
        super().__init__()
        self.anki_db_path = anki_db_path
        self.anki_db_field_indices = anki_db_field_indices
        self.anki_tags_to_exclude = anki_tags_to_exclude
        self.include_sound = include_sound
        self.media_dir_path = media_dir_path
        self.file_or_dir = file_or_dir
        self.file_to_scan = file_to_scan
        self.tag_for_new_cards = tag_for_new_cards
        self.output_path = output_path

    def run(self):
        orchestrateTextScanner(self.anki_db_path,
            self.anki_db_field_indices,
            self.anki_tags_to_exclude,
            self.include_sound,
            self.media_dir_path,
            self.file_or_dir,
            self.file_to_scan,
            self.tag_for_new_cards,
            self.output_path,
            self.sig)

def gatherControls(config):
    config_inputs = {
        'anki_db_path':'Path to the anki2 db file, or to any anki2 file such as from an unzipped .apkg file',
        'anki_db_field_indices':'',
        'media_dir_path':'',
        'file_or_dir':''
    }

    ui_inputs = {
        'anki_tags_to_exclude':'''<br><span><b>Tags to exclude:</b><br>
                A comma separated list of tags, these will be excluded from
                the de-duping process. That means the scanner will still
                consider a word to be new, even if it contains a character
                in one of your existing notes tagged with one of these tags</span>''',
        'include_sound':'''<br><span><b>Include sound files:</b><br>If this is true, the scanner will
                download sound files of the word readings and include them as media in the generated notes.</span>''',
        'output_path':'''<br><span><b>Output path:</b><br>Where the resulting .apk file should be placed
                (including the filename.apk)</span>''',
        'tag_for_new_cards':'''<br><span><b>Imported deck/tag name:</b><br>This string cannot contain
                spaces. It will be applied to all new notes as a tag,
                and will also be the name of the deck imported.</span>''',
        'file_to_scan':'''<br><span><b>File to scan:</b><br>This is the input file which
                will be scanned for new words. Note, it is possible to scan
                a whole collection of files at once by changing the file_or_dir
                property in the config to dir, and then putting the dir path here.</span>'''
    }

    hidden_cfg = {}
    for item in config_inputs:
        hidden_cfg[item] = config['textScanner'][item]['val']

    controls = []
    for ipt in ui_inputs:
        default = str(config['textScanner'][ipt]['val'])
        label = QLabel()
        label.setWordWrap(True)
        label.setText('\n'+ui_inputs[ipt])
        input = QLineEdit()
        input.setText(default)
        controls.append({"key":ipt, "label":label, "input":input})

    return controls, hidden_cfg

def showTextScanner():
    dialog = QDialog(mw)
    dialog.resize(900,800)
    dialog.setWindowTitle('Chinese Text Scanner')
    layout = QVBoxLayout()

    #buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
    #buttonBox.accepted.connect(dialog.accept)

    topLabel = QLabel()
    topLabel.setWordWrap(True)
    topLabel.setText('''<div style="font-weight: bold; font-size:24px; width: 5em; text-align:center;">
        Welcome to the Chinese Text Scanner!
        <br> 大家好，这是兔子先生的魔法扫描字器！
        </div><span>This will scan a text file, find any chinese words that contain
        new characters not already in the provided anki collection, and then produce
        an .apkg file which can be imported into anki. The import file will contain
        notes for all the new words, including tone colors and audio files powered
        by the chinese-support-redux project. Additional options are available in the config file.</span>''')
    #label.setOpenExternalLinks(True)

    spacer = QLabel()
    spacer.setText('')
    transmitBtn = QPushButton('Run the scan!')
    outputText = QTextBrowser()

    layout.addWidget(topLabel)
    controls, hidden_cfg = gatherControls(config)
    for control in controls:
        layout.addWidget(control['label'])
        layout.addWidget(control['input'])
    layout.addWidget(spacer)
    layout.addWidget(transmitBtn)
    layout.addWidget(outputText)
    #layout.addWidget(buttonBox)

    def updateTextOutput(text):
        outputText.append(text)

    def resetButton():
        transmitBtn.setEnabled(True)

    def runScanner():
        ui_inputs = {}
        for control in controls:
            ui_inputs[control['key']] = control['input'].text()
        ui_inputs['anki_tags_to_exclude'] = ui_inputs['anki_tags_to_exclude'].replace(" ","")
        transmitBtn.setEnabled(False)

        outputText.setText("Starting scan...")

        mw.worker = TextScannerThreadAsync(
            hidden_cfg['anki_db_path'],
            hidden_cfg['anki_db_field_indices'],
            ui_inputs['anki_tags_to_exclude'].split(','),
            str(ui_inputs['include_sound']),
            hidden_cfg['media_dir_path'],
            hidden_cfg['file_or_dir'],
            ui_inputs['file_to_scan'],
            ui_inputs['tag_for_new_cards'],
            ui_inputs['output_path'])
        mw.worker.sig.connect(updateTextOutput)
        mw.worker.finished.connect(resetButton)
        mw.worker.start()

    transmitBtn.clicked.connect(runScanner)

    dialog.setLayout(layout)
    dialog.exec_()
