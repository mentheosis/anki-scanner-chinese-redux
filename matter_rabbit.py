from chinese.database import Dictionary
from text_scanner import TextScanner

print("\nStarting\n")

dictionary = Dictionary()
sc = TextScanner(dictionary)

sc.scan_and_print('./text-files/diqitian/', './text-files/hsk_words.anki2', 1, 'dir')
sc.scan_and_print('./text-files/liulangdiqiu_liucixin.txt', './text-files/hsk_words.anki2', 1, 'file')
sc.scan_and_print('./text-files/santisanbuqu_liucixin.txt', './text-files/hsk_words.anki2', 1, 'file')

print("\ndone\n")
