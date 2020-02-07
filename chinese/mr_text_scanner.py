import os
import jieba
import re
from sqlite3 import connect

class ChineseNote:
    def __init__(self, word, simplified, traditional, sort_order=0, sentence="", count=0, frequency="unknown"):
        self.word = word
        self.simplified = simplified
        self.traditional = traditional
        self.sort_order = sort_order
        self.sentence = sentence
        self.count = count
        self.frequency = frequency

    def incrCount(self):
        self.count += 1

    def __str__(self):
         str = f"key:{self.word}, simplified:{self.simplified}, traditional:{self.traditional}"
         str=str+f"\nfirst_appearance_rank:{self.sort_order}, count_in_text:{self.count}"
         str=str+f"\nsentence:{self.sentence}"
         return str


class TextScanner:
    def __init__(self, dictionary, anki_db_file_path, anki_note_indices = [0], tags_to_exclude=[], outputQTTextBrowser=None):
        self.dictionary = dictionary
        self.anki_db_file_path = anki_db_file_path
        self.anki_note_indices = anki_note_indices
        self.tags_to_exclude = tags_to_exclude
        self.outputQTTextBrowser = outputQTTextBrowser

    ##############################
    ### Input text functions

    def parse_sentences_with_jieba(self, sentences):
        jieba_words = {}
        i = 1
        for text in sentences:
            #cut_all=False means "accurate mode" https://github.com/fxsjy/jieba
            seg_list = jieba.cut(text, cut_all=False)
            for word in seg_list:
                simp = self.dictionary._get_word(word,"simp")
                if simp != None:
                    if jieba_words.get(simp) == None:
                        trad = self.dictionary._get_word(word,"trad")
                        jieba_words[simp] = ChineseNote(word,simp,trad,i,text,1)
                        i += 1
                    else:
                        jieba_words[simp].incrCount()
        return jieba_words

    #param rel_path: relative path to unzipped epub director containing a bunch of xhtml
    def parse_unzipped_epub_to_dict(self, rel_path):
        #https://stackoverflow.com/questions/10377998/how-can-i-iterate-over-files-in-a-given-directory
        #directory_in_str = "./epubfile/"
        directory = os.fsencode(rel_path)

        booktext = []
        for file in os.listdir(directory):
             filename = os.fsdecode(file)
             if filename.endswith(".xhtml") or filename.endswith(".txt"):
                with open(rel_path+filename, 'r') as file:
                    data = re.split("[。，！？]",file.read().replace('\n', '').strip())
                    booktext.append(data)
             else:
                 continue
        return self.parse_sentences_with_jieba(booktext)


    def parse_single_file_to_dict(self, rel_path):
        #https://stackoverflow.com/questions/3114786/python-library-to-extract-epub-information/3114929
        with open(rel_path, 'r') as file:
            booktext = re.split("[。，！？]",file.read().replace('\n', '').strip())
        return self.parse_sentences_with_jieba(booktext)


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
    ## just a debugging method to explore anki file
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
        self.printOrLog("query",query)
        c.execute(query)
        already_have_words = {}
        for row in c:
            if query == 'select * from sqlite_master':
                self.printOrLog("row",row[1],row[1],row[2],row[3])
                sub_row = row[4].split("\n")
                for sub in sub_row:
                    self.printOrLog("subrow:",sub)
            else:
                self.printOrLog("row",row)

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

        query = "select flds, tags from notes"
        c.execute(query)
        already_have_words = {}
        for row in c:
            note_fields = row[0].split("\x1f")
            tags = row[1].split()
            exclude = False
            for exlcude in self.tags_to_exclude:
                if exlcude in tags:
                    exclude = True
            if exclude == False:
                for idx in self.anki_note_indices:
                    word = note_fields[idx]
                    simp = self.dictionary._get_word(word,"simp")
                    if simp != None and already_have_words.get(simp) == None:
                        trad = self.dictionary._get_word(word,"trad")
                        already_have_words[simp] = ChineseNote(word,simp,trad)
        return already_have_words

    ##############################
    ### De-duping comparison set functions

    def get_leftdiff_and_intersect(self, scanned_words, dedupe_list):
        leftdiff = {}
        intersect = {}
        for simp in scanned_words:
            if dedupe_list.get(simp) == None:
                #definition = self.dictionary.get_definitions(word,"en")
                leftdiff[simp] = scanned_words[simp]

            if dedupe_list.get(simp) != None:
                #definition = self.dictionary.get_definitions(word,"en")
                intersect[simp] = scanned_words[simp]
        return leftdiff, intersect

    def parse_chars_from_dict(self, dict):
        char_dict = {}
        for word in dict:
            for char in dict[word].simplified:
                char_dict[char] = char
        return char_dict

    # only return the subset of words that have a char from chars
    def get_words_using_chars(self, words, chars):
        new_char_words = {}
        for word in words:
            for char in words[word].simplified:
                if chars.get(char) != None:
                    new_char_words[word] = words[word]
        return new_char_words


    ##############################
    ### printing / entrypoint funtions

    def printOrLog(self,text=""):
        if self.outputQTTextBrowser != None:
            self.outputQTTextBrowser.append(text)
        else:
            print(text)

    def print_comparison_stats(self, leftname, rightname, left, right, new, overlap, noun):
        import json
        self.printOrLog()
        self.printOrLog(f'{len(right)} {noun}s in dedupe list {rightname}')
        self.printOrLog(f"{len(left)} {noun}s in {leftname}")
        #self.printOrLog("random word from those found:",str(list(left.values())[35]))
        self.printOrLog(f"{len(overlap)} overlap {noun}s")
        self.printOrLog(f"{len(new)} new {noun}s")
        #self.printOrLog(f"\nrandom new {noun}:",str(list(new.values())[36]))
        #self.printOrLog("\noverlap words:", overlap.keys())

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

        self.printOrLog(f"\n{text_path}")
        self.print_comparison_stats(text_path,self.anki_db_file_path, scanned_words, anki_words, left_diff, intersect, "word")
        self.print_comparison_stats(text_path,self.anki_db_file_path, scanned_chars, anki_chars, char_diff, char_intersect, "char")
        new_char_words = self.get_words_using_chars(left_diff,char_diff)
        self.printOrLog(f"{len(new_char_words)} words using new chars")
        if len(new_char_words) >=36:
            self.printOrLog(f"\nrandom new word: {str(list(new_char_words.values())[36])}")

        return new_char_words, left_diff, char_diff
