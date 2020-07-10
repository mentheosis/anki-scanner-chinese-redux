###################
## UI screens
from aqt import mw
from PyQt5.QtWidgets import QDialogButtonBox, QLabel, QVBoxLayout, QHBoxLayout, QButtonGroup, QFileDialog, QTextBrowser, QWidget, QPushButton, QAction, QLineEdit, QMessageBox, QRadioButton, QPlainTextEdit
from PyQt5 import QtCore, QtWidgets

import traceback
from .mr_async_worker_thread import TextScannerThreadAsync
from .mr_window import MatterRabbitWindow
from .singletons import config


##########################################################
# Util function for the scanner dialog window to gather up needed config and controls
##
def gatherControls(config, ui_mode="file"):
    config_inputs = {
        'anki_db_path':'',
        'anki_db_field_indices':'',
        'media_dir_path':'',
        'file_or_dir':'',
        'input_encoding':'',
        'target_note_type':'',
        'note_target_maps':''
    }

    ui_inputs = {
        'file_to_scan':'''<span><b>File to scan:</b><br>This is the input file which
                will be scanned for new words. Note, it is possible to scan
                a whole collection of files at once by changing the file_or_dir
                property in the config to dir, and then putting the dir path here.</span>''',
        'scan_mode':'''<br><span><b>Mode:</b><br>Choose whether to produce a card for every new words, every new inidividual character, or only new words using new characters</span>''',
        # replaced by auto-import
        #'output_path':'''<br><span><b>Output path:</b><br>Where the resulting .apkg file should be placed
        #        (including the filename.apkg)</span>''',
        'tag_for_new_cards':'''<br><span><b>Imported deck/tag name:</b><br>This string cannot contain
                spaces. It will be applied to all new notes as a tag,
                and will also be the name of the deck imported.</span>''',
        'anki_tags_to_exclude':'''<br><span><b>Tags to exclude:</b><br>
                A comma separated list of tags, the scanner will still
                consider a word to be new if its in your collection with one of these tags</span>''',
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
    if ui_mode == 'dev':
        label = QLabel()
        label.setWordWrap(True)
        label_text = '''<br><span><b>Query anki db:</b><br>You can run a sqlite query to probe the anki notes db.
                        Some common queries have been given easy aliases. Try running 'master' or 'models'</span>'''
        label.setText(label_text)
        query_input = QPlainTextEdit()
        controls.append({"key":"query_db", "label":label, "input":query_input})
    else:
        for ipt in ui_inputs:
            label = QLabel()
            label.setWordWrap(True)
            label.setText(ui_inputs[ipt])
            tryConfig = config['textScanner'].get(ipt)
            default = str(tryConfig['val']) if tryConfig != None else "Uninitialized"
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
                btnGrp = QButtonGroup()
                btnGrp.addButton(b1)
                btnGrp.addButton(b2)
                btnGrp.addButton(b3)
                radioLayout.addWidget(b1)
                radioLayout.addWidget(b2)
                radioLayout.addWidget(b3)

                scan_input = {"mode":default,"layout":radioLayout, "btnGrp":btnGrp}
                b1.toggled.connect(lambda:interpretRadioBtn(b1, scan_input))
                b2.toggled.connect(lambda:interpretRadioBtn(b2, scan_input))
                b3.toggled.connect(lambda:interpretRadioBtn(b3, scan_input))
                controls.append({"key":ipt, "label":label, "input":scan_input})
            elif ipt == 'file_to_scan' and ui_mode == 'clipboard':
                clipboard_input = QPlainTextEdit()
                label.setText("<span><b>Input text:</b></span>")
                controls.append({"key":ipt, "label":label, "input":clipboard_input})
            elif ipt == 'include_sound':
                sb1 = QRadioButton("True")
                sb1.mode = 'true'
                sb2 = QRadioButton("False")
                sb2.mode = 'false'

                if default == 'true':
                    sb1.setChecked(True)
                else:
                    sb2.setChecked(True)
                soundLayout = QHBoxLayout()
                btnGrp = QButtonGroup()
                btnGrp.addButton(sb1)
                btnGrp.addButton(sb2)
                soundLayout.addWidget(sb1)
                soundLayout.addWidget(sb2)

                sound_input = {"mode":default,"layout":soundLayout, "btnGrp":btnGrp}
                sb1.toggled.connect(lambda:interpretRadioBtn(sb1, sound_input))
                sb2.toggled.connect(lambda:interpretRadioBtn(sb2, sound_input))
                controls.append({"key":ipt, "label":label, "input":sound_input})
            else:
                input = QLineEdit()
                input.setText(default)
                controls.append({"key":ipt, "label":label, "input":input})

    return controls, hidden_cfg



#########################################################
# This is the main text scanning and dev-mode UI window
##
def showTextScanner(ui_mode="file"):
    mw.mr_worker = TextScannerThreadAsync()

    outerLayout = QVBoxLayout()
    colLayout = QHBoxLayout()
    leftLayout = QVBoxLayout()
    rightLayout = QVBoxLayout()
    outputText = QTextBrowser()

    topLabel = QLabel()
    topLabel.setWordWrap(True)
    topLabel.setText('''<div style="font-weight: bold; font-size:24px; width: 5em; text-align:center;">
        大家好，这是兔子先生的魔法扫描字器！</div>
        <div>Welcome to the Chinese Text Scanner! This will find any chinese words that are not already in your anki collection.
        It will then automatically import those words as notes into your collecton. Please be sure to configure your note types first, you can find the option in the text scanner menu.</div>
        <br>''')
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
        elif control['key'] == 'include_sound':
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

    scanButtonLayout = QHBoxLayout()

    if ui_mode == "dev":
        queryBtn = QPushButton('Run sqlite query')
        scanButtonLayout.addWidget(queryBtn)
    else:
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

    def resetButton():
        if mw.mr_worker.exiting == False and ui_mode != 'dev':
            scanBtn.setEnabled(True)
            cancelBtn.setEnabled(False)
            if hasattr(mw.mr_worker,'new_chars'):
                printBtn.setEnabled(True)
                noteBtn.setEnabled(True)

    def gather_ui_inputs():
        ui_inputs = {}
        for control in controls:
            if control['key'] == "scan_mode":
                ui_inputs[control['key']] = control['input']["mode"]
                config.config['textScanner'][control['key']]['val'] = control['input']['mode']
            elif control['key'] == "include_sound":
                ui_inputs[control['key']] = control['input']["mode"]
                config.config['textScanner'][control['key']]['val'] = control['input']['mode']
            elif control['key'] == 'file_to_scan' and ui_mode == 'clipboard':
                # dont save user input as config in this case
                ui_inputs[control['key']] = control['input'].toPlainText()
            elif control['key'] == 'anki_tags_to_exclude':
                ui_inputs['anki_tags_to_exclude'] = control['input'].text().replace(" ","")
                config.config['textScanner'][control['key']]['val'] = control['input'].text()
            elif control['key'] == 'query_db':
                ui_inputs[control['key']] = control['input'].toPlainText()
                if config.config['textScanner'].get(control['key']) == None:
                    config.config['textScanner'][control['key']] = {"val":''}
                config.config['textScanner'][control['key']]['val'] = control['input'].toPlainText()
            else:
                ui_inputs[control['key']] = control['input'].text()
                config.config['textScanner'][control['key']]['val'] = control['input'].text()
        # save user choices as their config for next time.
        config.save()
        return ui_inputs

    def onAnkiPackageReady(package):
        try:
            # creates a menu item in edit menu to undo
            checkString = f"TextScanner import {mw.mr_worker.importDeckName}"
            mw.checkpoint(checkString)
            package.write_to_collection_from_addon()
            # refreshes main view so new deck is visible
            mw.reset()
            updateTextOutput(f"Your new words have successfully been imported to anki!")
        except:
            e = traceback.format_exc()
            updateTextOutput(f"\nError: {e}")

    mw.mr_worker.sig.connect(updateTextOutput)
    mw.mr_worker.NotePackageSig.connect(onAnkiPackageReady)
    mw.mr_worker.finished.connect(resetButton)

    # dev mode sqlite query
    def runQuery():
        outputText.setText("")
        ui_inputs = gather_ui_inputs()
        mw.mr_worker.refresh_query(hidden_cfg['anki_db_path'],ui_inputs['query_db'])
        mw.mr_worker.setMode('query_db')
        mw.mr_worker.start()

    # the main file or text scan
    def runScanner():
        outputText.setText("Running the scan...")
        cancelBtn.setEnabled(True)
        printBtn.setEnabled(False)
        noteBtn.setEnabled(False)
        scanBtn.setEnabled(False)

        ui_inputs = gather_ui_inputs()

        mw.mr_worker.refresh_inputs(
            hidden_cfg['anki_db_path'],
            hidden_cfg['anki_db_field_indices'],
            ui_inputs['anki_tags_to_exclude'].split(','),
            str(ui_inputs['include_sound']),
            hidden_cfg['media_dir_path'],
            hidden_cfg['file_or_dir'],
            ui_inputs['file_to_scan'],
            ui_inputs['tag_for_new_cards'],
            #ui_inputs['output_path'],
            hidden_cfg['input_encoding'],
            hidden_cfg['target_note_type'],
            hidden_cfg['note_target_maps'],
            ui_inputs['scan_mode'])
        mw.mr_worker.setMode('scan')
        mw.mr_worker.start()

    def printWords():
        cancelBtn.setEnabled(True)
        printBtn.setEnabled(False)
        noteBtn.setEnabled(False)
        scanBtn.setEnabled(False)

        ui_inputs = gather_ui_inputs()

        mw.mr_worker.refresh_inputs(hidden_cfg['anki_db_path'],
            hidden_cfg['anki_db_field_indices'],
            ui_inputs['anki_tags_to_exclude'].split(','),
            str(ui_inputs['include_sound']),
            hidden_cfg['media_dir_path'],
            hidden_cfg['file_or_dir'],
            ui_inputs['file_to_scan'],
            ui_inputs['tag_for_new_cards'],
            #ui_inputs['output_path'],
            hidden_cfg['input_encoding'],
            hidden_cfg['target_note_type'],
            hidden_cfg['note_target_maps'],
            ui_inputs['scan_mode'])

        if ui_inputs['scan_mode'] == "new_chars":
            outputText.setText("Displaying characters ready for note creation")
        else:
            outputText.setText("Displaying words ready for note creation")

        mw.mr_worker.setMode('print')
        mw.mr_worker.start()

    def test():
        outputText.append("sdfsdfsdfssd!")

    def makeNotes():
        outputText.setText("")
        cancelBtn.setEnabled(True)
        printBtn.setEnabled(False)
        noteBtn.setEnabled(False)
        scanBtn.setEnabled(False)

        ui_inputs = gather_ui_inputs()
        # save this to display in the checkpoint string when importing
        mw.mr_worker.importDeckName = ui_inputs['tag_for_new_cards']

        mw.mr_worker.refresh_inputs(hidden_cfg['anki_db_path'],
            hidden_cfg['anki_db_field_indices'],
            ui_inputs['anki_tags_to_exclude'].split(','),
            str(ui_inputs['include_sound']),
            hidden_cfg['media_dir_path'],
            hidden_cfg['file_or_dir'],
            ui_inputs['file_to_scan'],
            ui_inputs['tag_for_new_cards'],
            #ui_inputs['output_path'],
            hidden_cfg['input_encoding'],
            hidden_cfg['target_note_type'],
            hidden_cfg['note_target_maps'],
            ui_inputs['scan_mode'])

        mw.mr_worker.setMode('make_notes')
        mw.mr_worker.start()

    def onCancel():
        resetButton()
        if hasattr(mw,'mr_worker'):
            mw.mr_worker.interrupt_and_quit = True
            mw.mr_worker.sig.emit("told worker to quit..")

    def onDialogClose():
        mw.mr_worker.exiting = True
        onCancel()

    if ui_mode == "dev":
        queryBtn.setStyleSheet("background-color: #8DE1DD")
        queryBtn.clicked.connect(runQuery)
    else:
        #scanBtn.clicked.connect(runScanner)
        scanBtn.clicked.connect(test)
        scanBtn.setStyleSheet("background-color: #8DE1DD")
        printBtn.clicked.connect(printWords)
        noteBtn.clicked.connect(makeNotes)
        cancelBtn.clicked.connect(onCancel)

    dialog = MatterRabbitWindow(outerLayout, onDialogClose, mw)
    dialog.resize(900,650)
    if ui_mode == "dev":
        dialog.setWindowTitle('Query DB')
    else:
        dialog.setWindowTitle('Chinese Text Scanner')
    dialog.show()
