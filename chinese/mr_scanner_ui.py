###################
## UI screens
from aqt import mw
from aqt.utils import askUser, showInfo
from anki.find import Finder

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout
from PyQt5.QtWidgets import QTextBrowser, QWidget, QPushButton, QAction, QLineEdit, QMessageBox

from os.path import dirname, join, realpath

from .singletons import dictionary, config
from .mr_text_scanner import TextScanner
from .mr_note_maker import NoteMaker

def orchestrateTextScanner(
    anki_db_path,
    anki_db_field_indices,
    anki_tags_to_exclude,
    media_dir_path,
    file_or_dir,
    file_to_scan,
    tag_for_new_cards,
    output_path,
    outputQTTextBrowser
    ):

    joined_db_path = join(dirname(realpath(__file__)),anki_db_path)
    sc = TextScanner(dictionary, joined_db_path, anki_db_field_indices, anki_tags_to_exclude, outputQTTextBrowser)
    nm = NoteMaker(dictionary, media_dir_path)

    new_char_words, new_words, new_chars = sc.scan_and_print(file_to_scan, file_or_dir)
    #nm.make_notes(new_char_words, tag_for_new_cards, output_path, tag_for_new_cards, include_sound=True)
    return "done"

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
        default = config['textScanner'][ipt]['val']
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
    layout = QVBoxLayout()

    #buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
    #buttonBox.accepted.connect(dialog.accept)

    topLabel = QLabel()
    topLabel.setWordWrap(True)
    topLabel.setText('''<div style="font-weight: bold; font-size:24px; width: 5em; text-align:center;">
        Welcome to The Material Rabbits' Automagical
        <br>Text Scanning Analyzer
        <br>大家好，这是事物兔子的自动魔法扫描章器！
        </div><span>This will scan a text file, find any chinese words that contain
        new characters not already in the provided anki collection, and then produce
        an .apkg file which can be imported into anki. The import file will contain
        notes for all the new words, including tone colors and audio files (provided
        by the chinese-support-redux addon)</span>''')
    #label.setOpenExternalLinks(True)

    spacer = QLabel()
    spacer.setText('')
    transmitBtn = QPushButton('Show text')
    outputText = QTextBrowser()
    outputText.setText("Hi browser")

    layout.addWidget(topLabel)
    controls, hidden_cfg = gatherControls(config)
    for control in controls:
        layout.addWidget(control['label'])
        layout.addWidget(control['input'])
    layout.addWidget(spacer)
    layout.addWidget(transmitBtn)
    layout.addWidget(outputText)
    #layout.addWidget(buttonBox)

    def fn():
        ui_inputs = {}
        for control in controls:
            ui_inputs[control['key']] = control['input'].text()
        transmitBtn.setEnabled(False)
        orchestrateTextScanner(
            hidden_cfg['anki_db_path'],
            hidden_cfg['anki_db_field_indices'],
            ui_inputs['anki_tags_to_exclude'],
            hidden_cfg['media_dir_path'],
            hidden_cfg['file_or_dir'],
            ui_inputs['file_to_scan'],
            ui_inputs['tag_for_new_cards'],
            ui_inputs['output_path'],
            outputText
        )
        #transmitBtn.setEnabled(True)
    transmitBtn.clicked.connect(fn)


    dialog.setLayout(layout)
    dialog.setWindowTitle('Text Scanning Analyzer')
    dialog.exec_()
