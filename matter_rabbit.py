from chinese.database import Dictionary
from chinese.mr_text_scanner import TextScanner
from chinese.mr_note_maker import NoteMaker
from os.path import dirname, join, realpath

print("\nStarting\n")

#####
# current expected usage:
# 1. get text file or dir of unzipped epup
# 2. export the anki deck you want to de-dedupe against
# 3. run this script with the relative paths to above filed in
# 4. import the resulting .apkg file
# 5. move the imported notes to your desired note-type and deck using anki ui
#####

anki_dedupe_file_path = './text-files/hsk_words.anki2'
text_to_scan = './text-files/liulangdiqiu_liucixin.txt'
text_is_file_or_dir = 'file'
output_apk_path = './import_this.apkg'

dictionary = Dictionary(external_mode=True)
anki_db_path = join(dirname(realpath(__file__)),anki_dedupe_file_path)
sc = TextScanner(dictionary, anki_db_path, 1)
nm = NoteMaker(dictionary)

#sc.query_anki_db("select models from col")
#new_char_words, new_words, new_chars = sc.scan_and_print('./text-files/diqitian/', 'dir')
#new_char_words, new_words, new_chars = sc.scan_and_print('./text-files/santisanbuqu_liucixin.txt', 'file')
new_char_words, new_words, new_chars = sc.scan_and_print(text_to_scan, text_is_file_or_dir)

nm.make_notes(new_char_words,output_apk_path)

print("\ndone\n")
