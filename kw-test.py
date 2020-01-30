# Based on: Chinese Support Redux Copyright © 2017-2018 Joseph Lorimer <joseph@lorimer.me>

print("\nStarting\n")

from chinese.database import Dictionary
import jieba

dictionary = Dictionary()


'''
big_text = "我来到了记忆之路的尽头，不管如何努力回想，在此之后没有任何情景，蛛丝马迹也没有。谭家鑫的眼睛瞪着我，以及随后的一声轰然巨响，这就是我能够寻找到的最后情景。</p><p>    在这个最后的情景里，我的身心沦陷在这个名叫李青的女人的自杀里，她是我曾经的妻子，是我的一段美好又心酸的记忆。我的悲伤还来不及出发，就已经到站下车。</p><p>    雪花还在飘落，浓雾还没散去，我仍然在行走。我在疲惫里越走越深，我想坐下来，然后就坐下了。我不知道是坐在椅子里，还是坐在石头上。我的身体摇摇晃晃坐在那里，像是超重的货船坐在波动的水面上。</p><p>    一个双目失明的死者手里拿着一根拐杖，敲击着虚无缥缈的地面走过来，走到我跟前站住脚，自言自语说这里坐着一个人。我说是的，这里是坐着一个人。他问我去殡仪馆怎么走？我问他有没有预约号。他拿出一张纸条给我看，上面印有A52。我说他可能走错方向了，应该转身往回走。他问我纸条上写着什么，我说是A52。他问是什么意思，我说到了殡仪馆要叫号的，你的号是A52。他点点头转身走去，拐杖敲击着没有回声的地面远去之后，我怀疑给这个双目失明的死者指错了方向，因为我自己正在迷失之中"


# TODO:
https://github.com/kerrickstaley/genankii
https://github.com/fxsjy/jieba
'''
'''
#if config['firstRun']:
# config['firstRun'] = False
#dictionary.create_indices()

# assume _get_word returns None if the string is not a valid word
def recurse_check_word(word,idx):
    res = dictionary._get_word(word,"simp")
    definition = dictionary.get_definitions(res,"en")
    no_match = res == None or definition == [] or definition == None
    if no_match and idx > 1:
        return recurse_check_word(word[0:idx-1],idx-1)
    if no_match:
        return None, None
    #print("result",res, dictionary.get_definitions(res,"en"))
    return res, definition

def recurse_check_big_text(text, start_idx):
    if start_idx < len(text):
        test_text = text[start_idx:start_idx+max_word]
        #print("test_text",test_text)
        res,df = recurse_check_word(test_text,max_word)
        if res != None:
            words_found[res] = ({"word":res, "definition":df})
        return recurse_check_big_text(text,start_idx+1)
    return None

def recurse_sentences(text,start_idx):
    return None

break_char = "。"
max_word = 4
words_found = {}
recurse_check_big_text(big_text,0)

print("input:",big_text);
print("\nresult:",len(words_found),"words")
print("\nrandom word from those found:",list(words_found.values())[35])

print("\n\nhere!")
word = words_found["我"]['word']
print("type",word, type(word))



'''
#### HERE ##########################################

'''
    def create_indices(self):
        self.c.execute(
            'CREATE INDEX IF NOT EXISTS isimplified ON cidian (simplified)'
        )
        self.c.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS itraditional '
            'ON cidian (traditional, pinyin)'
        )
        self.conn.commit()
'''

'''
CREATE TABLE sqlite_master (
  type TEXT,
  name TEXT,
  tbl_name TEXT,
  rootpage INTEGER,
  sql TEXT
);
'''





##############################
### Input text

import os

def parse_string_with_jieba(text):
    #cut_all=False means "accurate mode" https://github.com/fxsjy/jieba
    seg_list = jieba.cut(text, cut_all=False)
    jieba_words = {}
    for word in seg_list:
        res = dictionary._get_word(word,"simp")
        if res != None:
            jieba_words[res] = (res,None)
    return jieba_words

#param rel_path: relative path to unzipped epub director containing a bunch of xhtml
def parse_unzipped_epub_to_dict(rel_path):
    #https://stackoverflow.com/questions/10377998/how-can-i-iterate-over-files-in-a-given-directory
    #directory_in_str = "./epubfile/"
    directory = os.fsencode(rel_path)

    booktext = ""
    for file in os.listdir(directory):
         filename = os.fsdecode(file)
         if filename.endswith(".xhtml"):
            with open(directory_in_str+filename, 'r') as file:
                data = file.read().replace('\n', '')
                booktext += data
         else:
             continue
    return parse_string_with_jieba(booktext)


def parse_single_file_to_dict(rel_path):
    #https://stackoverflow.com/questions/3114786/python-library-to-extract-epub-information/3114929
    with open(rel_path, 'r') as file:
        booktext = file.read().replace('\n', '')
    return parse_string_with_jieba(booktext)


##############################
### De-duping comparison set

from os.path import dirname, join, realpath
from sqlite3 import connect

'''
file_path: path to an anki2 file, which is a sqllite file that
        comes from an unzipped anki .apckg
        it should be an export of a single deck / note type
key_index: the position in the anki note of the field which
        will be used as the key (e.g. the single word string)
        usually 0 or 1
'''
def load_dedupe_list(file_path, key_index = 0):
    db_path = join(dirname(realpath(__file__)),file_path)
    conn = connect(db_path)
    c = conn.cursor()

    #query = 'SELECT pinyin, pinyin_tw FROM cidian WHERE traditional=?'
    #query = 'select type tbl_name from SQLITE_MASTER'
    #query = 'select * from notes'
    #query = 'select sql from SQLITE_MASTER where tbl_name = "notes"'
    query = 'select distinct flds from notes'
    c.execute(query)

    already_have_words = {}
    for row in c:
        word = row[0].split("\x1f")[key_index]
        #print("\nparsed", word, row)
        already_have_words[word] = (None,None)
    return already_have_words


def get_leftdiff_and_intersect(scanned_words, dedupe_list):
    leftdiff = {}
    intersect = {}
    for word in scanned_words:
        if dedupe_list.get(word) == None:
            definition = dictionary.get_definitions(word,"en")
            leftdiff[word] = (word,definition)

        if already_have_words.get(word) != None:
            definition = dictionary.get_definitions(word,"en")
            intersect[word] = (word,definition)
    return leftdiff, intersect


#jieba_words = parse_unzipped_epub_to_dict()
jieba_words = parse_single_file_to_dict('./epubfile/diqitian/chapter_27478397.xhtml')

#file_path, key_index = "some_words.anki2", 0
file_path, key_index = "hsk_words.anki2", 1
already_have_words = load_dedupe_list(file_path, key_index)

new_words, overlap_words = get_leftdiff_and_intersect(jieba_words,already_have_words)

print("\ndeduping list size (hsk6):  ", len(already_have_words))
print("Jieba found words in text:  ", len(jieba_words) )  # 默认模式
#print("random word from those found:",list(jieba_words.values())[35])
print("new words:                  ", len(new_words))
print("overlap words:              ", len(overlap_words))
print("\nrandom new word:",list(new_words.values())[36])
#print("\noverlap words:", overlap_words.keys())

print("\ndone\n")
