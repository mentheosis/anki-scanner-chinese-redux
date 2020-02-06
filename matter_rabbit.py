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

#anki inputs
#anki_dedupe_file_path = './text-files/hsk_words.anki2'
anki_dedupe_file_path = "/home/kris/.local/share/Anki2/User 1/collection.anki2"
field_indices_to_use_in_anki_note = [0,1]
anki_tags_to_exclude = ["HSK6","exclude_from_dedupes","imported_from_流浪地球"]

#output
media_dir_path = './text-files/media/'
output_apk_path = './import_this.apkg'
tag_for_cards = "imported_from_流浪地球" #tags connot contain spaces
output_deck_name = tag_for_cards

#text input
#text_to_scan, file_or_dir = './text-files/diqitian/', 'dir'
#text_to_scan, file_or_dir = './text-files/santisanbuqu_liucixin.txt', 'file'
text_to_scan, file_or_dir = './text-files/liulangdiqiu_liucixin.txt', 'file'

# setup
dictionary = Dictionary()
anki_db_path = join(dirname(realpath(__file__)),anki_dedupe_file_path)
sc = TextScanner(dictionary, anki_db_path, field_indices_to_use_in_anki_note, anki_tags_to_exclude)
nm = NoteMaker(dictionary, media_dir_path)

# run
new_char_words, new_words, new_chars = sc.scan_and_print(text_to_scan, file_or_dir)
nm.make_notes(new_char_words, output_deck_name, output_apk_path, tag_for_cards, include_sound=True)

#sc.query_anki_db("select * from notes")
#sc.query_anki_db("select * from sqlite_master")
#words = sc.load_words_from_anki_notes()
#for word in words:
#    print(words[word])
#print("\ntest", len(words))

print("\ndone\n")
