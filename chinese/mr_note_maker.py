import genanki

class NoteMaker:
    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.note_model = genanki.Model(
            1091735104,
            'Import only model',
            fields=[
                {'name':'Hanzi'},
                {'name':'Simplified'},
                {'name':'Traditional'},
                {'name':'Pinyin'},
                #{'name':'Sound'},
                #{'name':'Ruby'},
                {'name':'Meaning'}, # detailed definition info, often coming from pleco
                #{'name':'Definition sparse'}, #used for reverse cards to hide extra definition info from pleco
                #{'name':'Classifier'},
                #{'name':'Color'},
                #{'name':'SentenceSimplified'},
                #{'name':'SentencePinyin'},
                #{'name':'SentenceMeaning'},
                #{'name':'SentenceAudio'},
                #{'name':'Frequency'}
            ],
            templates=[{
              'name': 'Import only card',
              'qfmt': '{{Hanzi}}',
              'afmt': '{{FrontSide}}<hr id="answer">{{Hanzi}}',
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

    # should return an array with same length as note_model.fields
    def enrich_word(self,word):
        simp = self.dictionary._get_word(word,"simp")
        trad = self.dictionary._get_word(word,"trad")
        definition = self.try_find_definition_by_char(word)
        pinyin = self.dictionary.get_pinyin(simp,'simp')

        res = [word,simp,trad,pinyin,definition]
        # print("res",res)
        return res

    def make_notes(self, words, out_path):
        deck = genanki.Deck(
            2059400110,
            'Import deck'
        )

        for word in words:
            deck.add_note(genanki.Note(self.note_model, self.enrich_word(word) ))

        print("\nNote maker is making a package")
        apkg = genanki.Package(deck)
        apkg.write_to_file(out_path)
        print("Note maker wrote to",out_path)
