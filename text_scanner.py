import os
import jieba
from os.path import dirname, join, realpath
from sqlite3 import connect

class TextScanner:
    def __init__(self, dictionary):
        self.dictionary = dictionary

    ##############################
    ### Input text functions

    def parse_string_with_jieba(self, text):
        #cut_all=False means "accurate mode" https://github.com/fxsjy/jieba
        seg_list = jieba.cut(text, cut_all=False)
        jieba_words = {}
        for word in seg_list:
            res = self.dictionary._get_word(word,"simp")
            if res != None:
                jieba_words[res] = (res,None)
        return jieba_words

    #param rel_path: relative path to unzipped epub director containing a bunch of xhtml
    def parse_unzipped_epub_to_dict(self, rel_path):
        #https://stackoverflow.com/questions/10377998/how-can-i-iterate-over-files-in-a-given-directory
        #directory_in_str = "./epubfile/"
        directory = os.fsencode(rel_path)

        booktext = ""
        for file in os.listdir(directory):
             filename = os.fsdecode(file)
             if filename.endswith(".xhtml"):
                with open(rel_path+filename, 'r') as file:
                    data = file.read().replace('\n', '')
                    booktext += data
             else:
                 continue
        return self.parse_string_with_jieba(booktext)


    def parse_single_file_to_dict(self, rel_path):
        #https://stackoverflow.com/questions/3114786/python-library-to-extract-epub-information/3114929
        with open(rel_path, 'r') as file:
            booktext = file.read().replace('\n', '')
        return self.parse_string_with_jieba(booktext)


    '''
    sql lite schema for reference
    CREATE TABLE sqlite_master (
      type TEXT,
      name TEXT,
      tbl_name TEXT,
      rootpage INTEGER,
      sql TEXT
    );
    '''
    '''
    file_path: path to an anki2 file, which is a sqllite file that
            comes from an unzipped anki .apckg
            it should be an export of a single deck / note type
    key_index: the position in the anki note of the field which
            will be used as the key (e.g. the single word string)
            usually 0 or 1
    '''
    def load_words_from_anki_notes(self, file_path, key_index = 0):
        db_path = join(dirname(realpath(__file__)),file_path)
        conn = connect(db_path)
        c = conn.cursor()

        #query = 'SELECT pinyin, pinyin_tw FROM cidian WHERE traditional=?'
        #query = 'select type tbl_name from SQLITE_MASTER'
        #query = 'select * from notes'
        #query = 'select sql from SQLITE_MASTER where tbl_name = "notes"'
        query = "select distinct flds from notes where tags not like '%HSK6%' "
        c.execute(query)

        already_have_words = {}
        for row in c:
            word = row[0].split("\x1f")[key_index]
            #print("\nparsed", word, row)
            already_have_words[word] = (None,None)
        return already_have_words

    ##############################
    ### De-duping comparison set functions

    def get_leftdiff_and_intersect(self, scanned_words, dedupe_list):
        leftdiff = {}
        intersect = {}
        for word in scanned_words:
            if dedupe_list.get(word) == None:
                definition = self.dictionary.get_definitions(word,"en")
                leftdiff[word] = (word,definition)

            if dedupe_list.get(word) != None:
                definition = self.dictionary.get_definitions(word,"en")
                intersect[word] = (word,definition)
        return leftdiff, intersect

    def parse_chars_from_dict(self, dict):
        char_dict = {}
        for word in dict:
            for char in word:
                char_dict[char] = (char,None)
        return char_dict

    # only return the subset of words that have a char from chars
    def get_words_using_chars(self, words, chars):
        new_char_words = {}
        for word in words:
            for char in word:
                if chars.get(char) != None:
                    new_char_words[word] = word
        return new_char_words

    def print_comparison_stats(self, leftname, rightname, left, right, new, overlap, noun):
        print('')#newline
        print(len(right), f' {noun} in dedupe list ({rightname})')
        print(len(left), f" {noun} in {leftname}:  ")
        #print("random word from those found:",list(jieba_words.values())[35])
        print(len(overlap), f" overlap {noun}")
        print(len(new), f" new {noun}")
        #print("\nrandom new word:",list(new_words.values())[36])
        #print("\noverlap words:", overlap_words.keys())
