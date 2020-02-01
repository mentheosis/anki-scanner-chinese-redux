from chinese.database import Dictionary
from chinese.mr_text_scanner import TextScanner
from chinese.mr_note_maker import NoteMaker
from os.path import dirname, join, realpath

print("\nStarting\n")

dictionary = Dictionary(external_mode=True)
anki_db_path = join(dirname(realpath(__file__)),'./text-files/hsk_words.anki2')
sc = TextScanner(dictionary, anki_db_path, 1)
nm = NoteMaker(dictionary)

#sc.query_anki_db("select models from col")
#new_char_words, new_words, new_chars = sc.scan_and_print('./text-files/diqitian/', 'dir')
#new_char_words, new_words, new_chars = sc.scan_and_print('./text-files/santisanbuqu_liucixin.txt', 'file')
new_char_words, new_words, new_chars = sc.scan_and_print('./text-files/liulangdiqiu_liucixin.txt', 'file')

nm.make_notes(new_char_words,'./import_this.apkg')

print("\ndone\n")
