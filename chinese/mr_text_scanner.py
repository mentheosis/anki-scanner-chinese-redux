import os
import jieba
from sqlite3 import connect

class TextScanner:
    def __init__(self, dictionary, anki_db_file_path, anki_note_key_index = 0):
        self.dictionary = dictionary
        self.anki_db_file_path = anki_db_file_path
        self.anki_note_key_index = anki_note_key_index

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
    def query_anki_db(self, query = 1):
        db_path = self.anki_db_file_path
        conn = connect(db_path)
        c = conn.cursor()

        if query == 1:
            #query = 'SELECT pinyin, pinyin_tw FROM cidian WHERE traditional=?'
            #query = 'select type tbl_name from SQLITE_MASTER'
            #query = 'select * from notes'
            #query = 'select sql from SQLITE_MASTER where tbl_name = "notes"'
            query = "select distinct flds from notes where tags not like '%HSK6%' "
        print("query",query)
        c.execute(query)
        already_have_words = {}
        for row in c:
            print("row",row)
            ''' # use for sqlite_master
            print("row",row[1],row[1],row[2],row[3])
            sub_row = row[4].split("\n")
            for sub in sub_row:
                print("subrow:",sub)
            '''

    '''
    file_path: path to an anki2 file, which is a sqllite file that
            comes from an unzipped anki .apckg
            it should be an export of a single deck / note type
    key_index: the position in the anki note of the field which
            will be used as the key (e.g. the single word string)
            usually 0 or 1
    '''
    def load_words_from_anki_notes(self):
        db_path = self.anki_db_file_path
        conn = connect(db_path)
        c = conn.cursor()

        query = "select distinct flds from notes where tags not like '%HSK6%' "
        c.execute(query)
        already_have_words = {}
        for row in c:
            word = row[0].split("\x1f")[self.anki_note_key_index]
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
                #definition = self.dictionary.get_definitions(word,"en")
                leftdiff[word] = (word,None)

            if dedupe_list.get(word) != None:
                #definition = self.dictionary.get_definitions(word,"en")
                intersect[word] = (word,None)
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


    ##############################
    ### printing / entrypoint funtions

    def print_comparison_stats(self, leftname, rightname, left, right, new, overlap, noun):
        #print(len(right), f' {noun} in dedupe list {rightname}')
        print(len(left), f" {noun} in {leftname}")
        #print("random word from those found:",list(jieba_words.values())[35])
        #print(len(overlap), f" overlap {noun}")
        print(len(new), f" new {noun}")
        #print("\nrandom new word:",list(new_words.values())[36])
        #print("\noverlap words:", overlap_words.keys())

    def scan_and_compare(self, text_path, file_or_dir="file"):
        anki_words = self.load_words_from_anki_notes()
        scanned_words = self.parse_unzipped_epub_to_dict(text_path) if file_or_dir == "dir" else self.parse_single_file_to_dict(text_path)
        left_diff, intersect = self.get_leftdiff_and_intersect(scanned_words, anki_words)

        anki_chars = self.parse_chars_from_dict(anki_words)
        scanned_chars = self.parse_chars_from_dict(scanned_words)
        char_diff, char_intersect = self.get_leftdiff_and_intersect(scanned_chars, anki_chars)

        return scanned_words, anki_words, left_diff, intersect, scanned_chars, anki_chars, char_diff, char_intersect

    def scan_and_print(self, text_path, file_or_dir="file"):
        scanned_words, anki_words, left_diff, intersect, scanned_chars, anki_chars, char_diff, char_intersect = self.scan_and_compare(
            text_path,
            file_or_dir
        )
        print(f"\n{text_path}")
        self.print_comparison_stats(text_path,self.anki_db_file_path, scanned_words, anki_words, left_diff, intersect, "words")
        self.print_comparison_stats(text_path,self.anki_db_file_path, scanned_chars, anki_chars, char_diff, char_intersect, "chars")
        new_char_words = self.get_words_using_chars(left_diff,char_diff)
        print(len(new_char_words),"words using new chars")
        return new_char_words, left_diff, char_diff
