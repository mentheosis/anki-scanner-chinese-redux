import genanki
from os.path import join
from .freq import get_frequency
from .behavior import get_classifier, find_colors
from .sound import sound_with_path

class NoteMaker:
    def __init__(self, dictionary, external_media_path):
        self.dictionary = dictionary
        self.external_media_path = external_media_path
        self.note_model = genanki.Model(
            1091735104,
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
                #{'name':'SentenceSimplified'},
                #{'name':'SentencePinyin'},
                #{'name':'SentenceMeaning'},
                #{'name':'SentenceAudio'},
                {'name':'Frequency'}
            ],
            templates=[{
              'name': 'Import only card',
              'qfmt': '{{Hanzi}}',
              'afmt': '{{FrontSide}}<hr id="answer">{{Meaning}}<br>{{Sound}}',
              'css':'''.tone1 {color: red;}
                        .tone2 {color: orange;}
                        .tone3 {color: #1510f0;}
                        .tone4 {color: #42a7f9;}
                        .tone5 {color: gray;}'''
            }])

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
    def enrich_word(self, word, include_sound):
        simp = self.dictionary._get_word(word,"simp")
        trad = self.dictionary._get_word(word,"trad")
        definition = self.try_find_definition_by_char(word)
        pinyin = self.dictionary.get_pinyin(simp,'simp')
        color_pinyin = find_colors(pinyin,{"pinyin":pinyin})

        classifier = get_classifier(word, [])
        color = find_colors(word,{"pinyin":pinyin})
        frequency = get_frequency(word)

        sound=''
        media_path = ''
        if include_sound:
            #"google|zh-cn"
            #"google|zh-tw"
            sound, media_path = self.find_sound(word,"google|zh-tw")

        res = [word, simp, trad, color_pinyin, sound, definition, classifier, color, frequency]
        return res, join(self.external_media_path,media_path)

    def make_notes(self, words, out_path, tag, include_sound=False):
        deck = genanki.Deck(
            2059400110,
            'Import deck'
        )

        print("\nNote maker is now gathering enrichment data for the words, this may take a while...")
        i = 0
        media_paths = []
        for word in words:
            i+=1
            if i%25 == 0:
                print(f"{i} words enriched")
            note, media_path = self.enrich_word(word, include_sound)
            media_paths.append(media_path)
            deck.add_note(genanki.Note( self.note_model, note, tags=[tag]))

        print("Note maker is making a package")
        apkg = genanki.Package(deck)
        if include_sound == True:
            apkg.media_files = media_paths
        apkg.write_to_file(out_path)
        print("Note maker wrote to",out_path)
