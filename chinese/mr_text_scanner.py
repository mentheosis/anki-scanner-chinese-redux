import os, json, traceback
from os.path import dirname, join, realpath
from sqlite3 import connect
import jieba
import re
from .mr_anki_db_client import AnkiDbClient


class ChineseNote:
    def __init__(self, word, simplified, traditional, pinyin="", definition="", sort_order=0, sentence="", count=0, frequency="unknown"):
        self.word = word
        self.simplified = simplified
        self.traditional = traditional
        self.pinyin = pinyin
        self.definition = definition
        self.sort_order = sort_order
        self.sentence = sentence
        self.count = count
        self.frequency = frequency

    def incrCount(self, incr=1):
        self.count += incr

    def __str__(self):
         str = f"Simplified: {self.simplified}, Traditional: {self.traditional}, Pinyin: {self.pinyin}\n"
         str=str+f"First appearance: {self.sort_order}, Count in text: {self.count}\n"
         str=str+f"Sentence: {self.sentence}\n"
         return str

sentence_delimiters = "[。，！？><]"

class TextScanner:
    def __init__(self, dictionary, anki_db_file_path, anki_note_indices = [0,1], tags_to_exclude=[], emitter=None, thread_obj=None):
        self.dictionary = dictionary
        self.anki_db_file_path = anki_db_file_path
        self.anki_note_indices = anki_note_indices
        self.tags_to_exclude = tags_to_exclude
        self.emitter = emitter
        self.thread_obj = thread_obj
        self.newDbClient = AnkiDbClient(anki_db_file_path, self.printOrLog)

    def printOrLog(self,text=""):
        if self.emitter != None and self.thread_obj != None and self.thread_obj.interrupt_and_quit == False:
            self.emitter.emit(text)
        else:
            print(text)

    ##############################
    ### Input text functions

    def try_find_definition_by_char(self,word):
        lookup = self.dictionary.get_definitions(word,"en")
        definition = ""
        if len(lookup) != 0:
            definition = lookup[0][1]
        if len(lookup) == 0 and len(word) > 0:
            definition = "by char: "
            for char in word:
                if char != "一":
                    char_lookup = self.dictionary.get_definitions(char,"en")
                    if len(char_lookup) != 0:
                        definition += "<br><br>"+char+"<br>"+char_lookup[0][1]
        return definition

    def word_has_new_char(self, word):
        if hasattr(self,'anki_chars'):
            for char in word:
                if self.anki_chars.get(char) == None:
                    return True
            return False
        else:
            # if we haven't loaded the anki_chars, then consider the word new
            return True

    ## because jieba sometimes parses words that are not found in our dictionary,
    # we need to be careful not to throw away words and charactes from text
    # just because our dictionary doesnt have an entry.
    #
    # This function will use our dictionary if possible for simplified and traditional split
    # but will fall back on the scanned word itself at least. We should always be able to find pinyin too
    #
    # If the word is determine to not be chinese at all, this will return None, None
    # otherwise returns Simplfied, Traditional
    def try_get_word_basics(self,word):
        # we can skip trying to futher process things like punctuation, numbers, etc
        # by checking if the first character is in our dictionary
        isChineseOrNot = self.dictionary._get_word(word[0],"simp")
        if isChineseOrNot != None:
            simp = self.dictionary._get_word(word,"simp")
            if simp != None:
                trad = self.dictionary._get_word(word,"trad")
            else:
                # in this case the Jieba dictionary found a word that our dictionary doesn't know
                # we'll check if it contains new characters, and if so at least get the pinyin and below get the per-character definition.
                if self.word_has_new_char(word):
                    simp = word
                    trad = word
                else:
                    # in this case, the dictionary didnt know the word, and it had no new characters, so its probably
                    # a trivial combination, a common proper noun, or some junk that jieba got wrong
                    return None, None
            return simp, trad
        else:
            return None, None

    def parse_sentences_with_jieba(self, sentences):
        jieba_words = {}
        i = 0
        self.printOrLog(f"Total sentences delimited by '{sentence_delimiters}': {len(sentences)}")
        total_words = 0
        for text in sentences:
            if self.thread_obj != None and self.thread_obj.interrupt_and_quit == True:
                break
            #cut_all=False means "accurate mode" https://github.com/fxsjy/jieba
            seg_list = jieba.cut(text, cut_all=False)
            for word in seg_list:
                total_words += 1
                simp, trad = self.try_get_word_basics(word)
                if simp != None:
                    i += 1
                    if jieba_words.get(simp) == None:
                        pinyin = self.dictionary.get_pinyin(simp,'simp')
                        definition = self.try_find_definition_by_char(simp)
                        jieba_words[simp] = ChineseNote(word,simp,trad,pinyin,definition,i,text,1)
                    else:
                        jieba_words[simp].incrCount()

        self.printOrLog(f"Total words: {total_words}")
        return jieba_words

    #param rel_path: relative path to unzipped epub director containing a bunch of xhtml
    def parse_unzipped_epub_to_dict(self, rel_path, encoding="utf-8"):
        #https://stackoverflow.com/questions/10377998/how-can-i-iterate-over-files-in-a-given-directory
        #directory_in_str = "./epubfile/"
        directory = os.fsencode(rel_path)

        booktext = []
        for file in os.listdir(directory):
             filename = os.fsdecode(file)
             if filename.endswith(".xhtml") or filename.endswith(".txt"):
                try:
                    with open(rel_path+filename, 'r', encoding=encoding) as file:
                        data = re.split(sentence_delimiters,file.read().replace('\n', '').strip())
                        booktext.append(data)
                except:
                    self.printOrLog(f"Could not open the file {path}, make sure it exists.")
             else:
                 continue
        return self.parse_sentences_with_jieba(booktext)


    def parse_single_file_to_dict(self, rel_path, encoding="utf-8"):
        #https://stackoverflow.com/questions/3114786/python-library-to-extract-epub-information/3114929
        path = join(dirname(realpath(__file__)),rel_path)
        try:
            with open(path, 'r', encoding=encoding) as file:
                booktext = re.split(sentence_delimiters,file.read().replace('\n', '').strip())
        except:
            self.printOrLog(f"Could not open the file {path}, make sure it exists.")
            return {}
        return self.parse_sentences_with_jieba(booktext)

    def parse_rawtext_to_dict(self, raw_text, encoding="utf-8"):
        sentences = re.split(sentence_delimiters,raw_text.replace('\n', '').strip())
        return self.parse_sentences_with_jieba(sentences)


    ## just a debugging method to explore anki file
    def query_db(self, query):
        if query[0:9] == 'show tag ':
            self.newDbClient.show_words_with_tag(query, self.dictionary, self.anki_note_indices)
        else:
            self.newDbClient.query_db(query)


    '''
    file_path: path to an anki2 file, which is a sqllite file that
            comes from an unzipped anki .apckg
            it should be an export of a single deck / note type
    key_index: the position in the anki note of the field which
            will be used as the key (e.g. the single word string)
            usually 0 or 1
    '''
    def load_words_from_anki_notes(self):
        try:
            db_path = self.anki_db_file_path
            conn = connect(db_path)
            c = conn.cursor()
        except:
            self.printOrLog("Could not open your anki collection, try changing the anki_db_path in the config file of this addon.")
            return {}

        query = "select flds, tags from notes"
        c.execute(query)
        already_have_words = {}
        for row in c:
            note_fields = row[0].split("\x1f")
            tags = row[1].split()
            exclude = False
            for tag in self.tags_to_exclude:
                # tags should already be stripped of white spaces
                #tag = tag.strip()
                if tag in tags:
                    exclude = True
            if exclude == False:
                for idx in self.anki_note_indices:
                    word = note_fields[idx]
                    simp, trad = self.try_get_word_basics(word)
                    if simp != None and already_have_words.get(simp) == None:
                        pinyin = self.dictionary.get_pinyin(simp,'simp')
                        already_have_words[simp] = ChineseNote(word,simp,trad,pinyin)
        self.anki_words = already_have_words
        self.anki_chars = self.parse_chars_from_dict(self.anki_words)
        return self.anki_words

    ##############################
    ### De-duping comparison set functions

    def get_leftdiff_and_intersect(self, scanned_words, dedupe_list):
        leftdiff = {}
        intersect = {}
        for simp in scanned_words:
            if dedupe_list.get(simp) == None:
                leftdiff[simp] = scanned_words[simp]

            if dedupe_list.get(simp) != None:
                intersect[simp] = scanned_words[simp]
        return leftdiff, intersect

    def parse_chars_from_dict(self, dict):
        char_dict = {}
        for word in dict:
            for char in dict[word].simplified:
                simp = self.dictionary._get_word(char,"simp")
                if simp != None:
                    if char_dict.get(simp) == None:
                        trad = self.dictionary._get_word(char,"trad")
                        pinyin = self.dictionary.get_pinyin(simp,'simp')

                        lookup = self.dictionary.get_definitions(word,"en")
                        definition = ""
                        if len(lookup) != 0:
                            definition = lookup[0][1]

                        sort_order = dict[word].sort_order
                        count = dict[word].count
                        sentence = dict[word].sentence
                        char_dict[simp] = ChineseNote(char,simp,trad,pinyin,definition,sort_order,sentence,count)
                    else:
                        char_dict[simp].incrCount(dict[word].count)
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

    def print_comparison_stats(self, leftname, rightname, left, right, new, overlap, noun):
        self.printOrLog()
        self.printOrLog(f'{len(right)} {noun}s in existing collection')
        self.printOrLog(f"{len(left)} {noun}s in input")
        #self.printOrLog("random word from those found:",str(list(left.values())[35]))
        self.printOrLog(f"{len(overlap)} overlap {noun}s")
        self.printOrLog(f"{len(new)} new {noun}s")
        #self.printOrLog(f"\nrandom new {noun}:",str(list(new.values())[36]))
        #self.printOrLog("\noverlap words:", overlap.keys())

    def scan_and_compare(self, text_path, file_or_dir="file", encoding="utf-8"):
        self.load_words_from_anki_notes()

        if file_or_dir == "dir":
            scanned_words = self.parse_unzipped_epub_to_dict(text_path, encoding)
        elif file_or_dir == "clipboard":
            scanned_words = self.parse_rawtext_to_dict(text_path, encoding)
        else:
            scanned_words = self.parse_single_file_to_dict(text_path, encoding)

        left_diff, intersect = self.get_leftdiff_and_intersect(scanned_words, self.anki_words)

        scanned_chars = self.parse_chars_from_dict(scanned_words)
        char_diff, char_intersect = self.get_leftdiff_and_intersect(scanned_chars, self.anki_chars)

        return scanned_words, self.anki_words, left_diff, intersect, scanned_chars, self.anki_chars, char_diff, char_intersect

    def scan_and_print(self, text_path, file_or_dir="file", encoding="utf-8", scan_mode="new_char_words"):
        scanned_words, anki_words, left_diff, intersect, scanned_chars, anki_chars, char_diff, char_intersect = self.scan_and_compare(
            text_path,
            file_or_dir
        )

        self.printOrLog(f"Scanning:\n{text_path}")
        def printAll():
            self.print_comparison_stats(text_path,self.anki_db_file_path, scanned_words, anki_words, left_diff, intersect, "word")
            self.print_comparison_stats(text_path,self.anki_db_file_path, scanned_chars, anki_chars, char_diff, char_intersect, "char")
        printAll()
        new_char_words = self.get_words_using_chars(left_diff,char_diff)
        self.printOrLog(f"{len(new_char_words)} words using new chars")

        if scan_mode == "new_chars":
            self.printOrLog(f"\nUsing mode 'new_chars', found {len(char_diff)} new characters")
            if len(char_diff) >=2:
                self.printOrLog(f"Random new character: {str(list(char_diff.values())[2])}")
        elif scan_mode == "new_words":
            self.printOrLog(f"\nUsing mode 'new_words', found {len(left_diff)} new words")
            if len(left_diff) >=12:
                self.printOrLog(f"Random new word: {str(list(left_diff.values())[12])}")
        else:
            self.printOrLog(f"\nUsing mode 'new_char_words', found {len(new_char_words)} new words using new characters")
            if len(new_char_words) >=12:
                self.printOrLog(f"Random new word: {str(list(new_char_words.values())[12])}")

        return new_char_words, left_diff, char_diff, printAll
