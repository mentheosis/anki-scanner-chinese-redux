from chinese.database import Dictionary
from text_scanner import TextScanner

print("\nStarting\n")

dictionary = Dictionary()
sc = TextScanner(dictionary)

#jieba_words = parse_single_file_to_dict('./text-files/diqitian/chapter_27478397.xhtml')
#file_path, key_index = "some_words.anki2", 0
file_path, key_index = "./text-files/hsk_words.anki2", 1

hsk6 = sc.load_words_from_anki_notes(file_path, key_index)
diqitian = sc.parse_unzipped_epub_to_dict('./text-files/diqitian/')

diqi_new_hsk, diqi_overlap_hsk = sc.get_leftdiff_and_intersect(diqitian, hsk6)
sc.print_comparison_stats("第七天","HSK5", diqitian, hsk6, diqi_new_hsk, diqi_overlap_hsk, "words")

hsk_chars = sc.parse_chars_from_dict(hsk6)
diqi_chars = sc.parse_chars_from_dict(diqitian)
diqi_new_chars, diqi_overlap_chars = sc.get_leftdiff_and_intersect(diqi_chars, hsk_chars)
sc.print_comparison_stats("第七天","HSK5", diqi_chars, hsk_chars, diqi_new_chars, diqi_overlap_chars, "chars")

print("")
diqi_new_char_words = sc.get_words_using_chars(diqi_new_hsk, diqi_new_chars)
print(len(diqi_new_char_words)," words from 第七天 using non-hsk chars")

#for word in diqi_new_char_words:
#    print(word)

#guichuideng = sc.parse_unzipped_epub_to_dict('./text-files/guichuideng/')

#diqi_new_hsk, diqi_overlap_hsk = sc.get_leftdiff_and_intersect(diqitian, hsk6)
#sc.print_comparison_stats("第七天","HSK6", diqitian, hsk6, diqi_new_hsk, diqi_overlap_hsk, "words")

#gui_new_hsk, gui_overlap_hsk = sc.get_leftdiff_and_intersect(guichuideng, hsk6)
#sc.print_comparison_stats("鬼吹灯","HSK6", guichuideng, hsk6, gui_new_hsk, gui_overlap_hsk, "words")

#diqi_new_gui, diqi_overlap_gui = sc.get_leftdiff_and_intersect(diqitian, guichuideng)
#sc.print_comparison_stats("第七天","鬼吹灯", diqitian, guichuideng, diqi_new_gui, diqi_overlap_gui, "words")

print("\ndone\n")
