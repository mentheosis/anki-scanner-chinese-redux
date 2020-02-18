import genanki
from os.path import dirname, join, realpath
from .freq import get_frequency
from .behavior import get_classifier, find_colors
from .sound import sound_with_path

class NoteMaker:
    def __init__(self, dictionary, external_media_path, emitter=None, thread_obj=None):
        self.dictionary = dictionary
        self.external_media_path = external_media_path
        self.emitter = emitter
        self.thread_obj = thread_obj
        self.note_model = genanki.Model(
            1091337104,
            'Import only model',
            fields=[
                {'name':'Hanzi'},
                {'name':'Simplified'},
                {'name':'Traditional'},
                {'name':'Pinyin'},
                {'name':'Sound'},
                #{'name':'Ruby'},
                {'name':'Meaning'}, # detailed definition info, often coming from pleco
                #{'name':'Definition sparse'}, #used for reverse cards to hide extra definition info from pleco
                {'name':'Classifier'},
                {'name':'Color'},
                {'name':'Sentence'},
                {'name':'SentencePinyin'},
                #{'name':'SentenceMeaning'},
                #{'name':'SentenceAudio'},
                {'name':'sort'},
                {'name':'Frequency'}
            ],
            templates=[{
              'name': 'Import only card',
              'qfmt': '<div class=hanzi>{{Hanzi}}</div><br><br><div class=sentence>{{Sentence}}</div>',
              'afmt': '<div class=hanzi>{{Color}}</div><br><div class=pinyin>{{Pinyin}}</div><br>{{Meaning}}<br><br><div class=sentence>{{Sentence}}</div><br><div class=sentence>{{SentencePinyin}}</div>',
            }],
            css = '.card {font-family: arial; font-size: 22px; text-align: left;  background-color: #fdf6e3;} .hanzi {font-family: Kaiti;  font-size: 50px; line-height: 0.8em, margin-top:0.2em; font-weight:normal;} .tone1 {color: red;} .tone2 {color: orange;} .tone3 {color: #1510f0;} .tone4 {color: #42a7f9;} .tone5 {color: gray;}'
)

    def printOrLog(self,text=""):
        if self.emitter != None and self.thread_obj != None and self.thread_obj.interrupt_and_quit == False:
            self.emitter.emit(text)
        else:
            print(text)

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
                        definition += "<br><br>"+char_lookup[0][1]
        return definition

    def find_sound(self, hanzi, speech_type="config"):
        speech = config['speech'] if speech_type == "config" else speech_type
        s, path = sound_with_path(hanzi, speech, self.external_media_path)
        if s:
            return s, path
        else:
            return "error finding sound",''

    # should return an array with same length as note_model.fields
    def enrich_word(self, rawNote, include_sound):
        simp = rawNote.simplified
        trad = rawNote.traditional
        definition = self.try_find_definition_by_char(rawNote.word)
        pinyin = self.dictionary.get_pinyin(simp,'simp')
        color_pinyin = find_colors(simp,{"pinyin":pinyin},pinyinMode=True,dictionary=self.dictionary)

        sentence_pinyin = self.dictionary.get_pinyin(rawNote.sentence,'simp')
        sentence_color_pinyin = find_colors(sentence_pinyin,{"pinyin":sentence_pinyin})

        classifier = get_classifier(rawNote.word, [], self.dictionary)
        color = find_colors(rawNote.word,{"pinyin":pinyin})
        frequency = get_frequency(rawNote.word)

        sound=''
        media_path = ''
        if include_sound == True:
            #"google|zh-cn"
            #"google|zh-tw"
            sound, media_path = self.find_sound(rawNote.word,"google|zh-tw")

        # all fields must be strings
        res = [rawNote.word, simp, trad, color_pinyin, sound, definition,
                classifier, color, rawNote.sentence, sentence_color_pinyin,
                str(rawNote.sort_order), frequency]
        assert len(res) == len(self.note_model.fields)
        return res, join(dirname(realpath(__file__)),self.external_media_path,media_path)

    # @param rawNoteDict should be a dictionary of ChineseNote objects from ./mr_text_scanner.py
    def make_notes(self, rawNoteDict, deck_name, out_path, tag, include_sound=False):
        deck = genanki.Deck(
            2051337110,
            deck_name
        )

        self.printOrLog("\nNote maker is now gathering enrichment data for the words, this may take a while, especially if you are including audio files. The scanner will update progress here every 25 words...")
        i = 0
        media_paths = []
        for simp in rawNoteDict:
            if self.thread_obj != None and self.thread_obj.interrupt_and_quit == True:
                break
            i+=1
            if i%25 == 0:
                self.printOrLog(f"{i} words enriched")
            note, media_path = self.enrich_word(rawNoteDict[simp], include_sound)
            media_paths.append(media_path)
            deck.add_note(genanki.Note( self.note_model, note, tags=[tag]))

        if self.thread_obj != None and self.thread_obj.interrupt_and_quit == True:
            return
        self.printOrLog("Note maker is making a package")
        apkg = genanki.Package(deck)
        if include_sound == True:
            apkg.media_files = media_paths
        apkg.write_to_file(out_path)
        self.printOrLog(f"Note maker wrote {len(rawNoteDict)} new notes to to {join(dirname(realpath(__file__)),out_path)}")
