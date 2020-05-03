from PyQt5 import QtCore, QtWidgets
from .mr_text_scanner import TextScanner
from .mr_note_maker import NoteMaker
from .database import Dictionary
from os.path import dirname, join, realpath
import genanki

class TextScannerThreadAsync(QtCore.QThread):
    sig = QtCore.pyqtSignal(str)
    NotePackageSig = QtCore.pyqtSignal(genanki.Package)

    def __init__(self):
        super().__init__()
        # internal default params
        self.interrupt_and_quit = False
        self.exiting = False
        self.run_mode = "scan"

    def refresh_query(self, anki_db_path, query):
        self.anki_db_path = anki_db_path
        self.query = query

    def refresh_inputs(self,
    anki_db_path,
    anki_db_field_indices,
    anki_tags_to_exclude,
    include_sound,
    media_dir_path,
    file_or_dir,
    file_to_scan,
    tag_for_new_cards,
    #output_path,
    input_encoding,
    target_note_type,
    note_target_maps,
    scan_mode):
        self.anki_db_path = anki_db_path
        self.anki_db_field_indices = anki_db_field_indices
        self.anki_tags_to_exclude = anki_tags_to_exclude
        self.include_sound = include_sound
        self.media_dir_path = media_dir_path
        self.file_or_dir = file_or_dir
        self.file_to_scan = file_to_scan
        self.tag_for_new_cards = tag_for_new_cards
        self.output_path = None #output_path
        self.input_encoding = input_encoding
        self.target_note_type = target_note_type
        self.note_target_maps = note_target_maps
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

        elif self.run_mode == 'get_existing_note_types':
            dictionary = Dictionary()
            joined_db_path = join(dirname(realpath(__file__)),self.anki_db_path)
            nm = NoteMaker(dictionary, None, joined_db_path, None, None, self.sig, self)
            self.note_models = nm.get_anki_note_models()
            #nm.display_existing_node_models()
            self.nm_fields = nm.generated_fields

        elif self.run_mode == 'make_notes':
            dictionary = Dictionary()
            joined_db_path = join(dirname(realpath(__file__)),self.anki_db_path)
            nm = NoteMaker(dictionary, self.media_dir_path, joined_db_path, self.target_note_type, self.note_target_maps, self.sig, self)

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
            package = nm.make_notes(new_notes, self.tag_for_new_cards, self.output_path, self.tag_for_new_cards, include_sound)
            if package != None:
                self.NotePackageSig.emit(package)
            else:
                self.sig.emit("\nCould not create anki package")

            if self.interrupt_and_quit == False:
                self.sig.emit("\nThanks for using the scanner!")
            else:
                self.sig.emit("\nExiting early, no package made, thanks for using the scanner!")
            dictionary.conn.close()

        elif self.run_mode == 'query_db':
            # worker thread needs its own dictionry, so cant use singleton here
            dictionary = Dictionary()
            joined_db_path = join(dirname(realpath(__file__)),self.anki_db_path)
            sc = TextScanner(dictionary, joined_db_path, [], [], self.sig, self)
            sc.query_db(self.query)
            dictionary.conn.close()

        else:
            self.sig.emit(f"Worker thread has nothing to do for mode {self.run_mode}...")
