# Based on: Chinese Support Redux Copyright © 2017-2018 Joseph Lorimer <joseph@lorimer.me>

print("\nStarting\n")

from chinese.database import Dictionary

dictionary = Dictionary()

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


big_text = "我来到了记忆之路的尽头，不管如何努力回想，在此之后没有任何情景，蛛丝马迹也没有。谭家鑫的眼睛瞪着我，以及随后的一声轰然巨响，这就是我能够寻找到的最后情景。</p><p>    在这个最后的情景里，我的身心沦陷在这个名叫李青的女人的自杀里，她是我曾经的妻子，是我的一段美好又心酸的记忆。我的悲伤还来不及出发，就已经到站下车。</p><p>    雪花还在飘落，浓雾还没散去，我仍然在行走。我在疲惫里越走越深，我想坐下来，然后就坐下了。我不知道是坐在椅子里，还是坐在石头上。我的身体摇摇晃晃坐在那里，像是超重的货船坐在波动的水面上。</p><p>    一个双目失明的死者手里拿着一根拐杖，敲击着虚无缥缈的地面走过来，走到我跟前站住脚，自言自语说这里坐着一个人。我说是的，这里是坐着一个人。他问我去殡仪馆怎么走？我问他有没有预约号。他拿出一张纸条给我看，上面印有A52。我说他可能走错方向了，应该转身往回走。他问我纸条上写着什么，我说是A52。他问是什么意思，我说到了殡仪馆要叫号的，你的号是A52。他点点头转身走去，拐杖敲击着没有回声的地面远去之后，我怀疑给这个双目失明的死者指错了方向，因为我自己正在迷失之中"

break_char = "。"
max_word = 4
words_found = {}
recurse_check_big_text(big_text,0)

print("input:",big_text);
print("\nresult:",len(words_found),"words")
print("\nrandom word from those found:",list(words_found.values())[35])

print("\ndone\n")
