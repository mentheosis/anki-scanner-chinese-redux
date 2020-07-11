import genanki
import traceback, json
from os.path import dirname, join, realpath
from .freq import get_frequency
from .behavior import get_classifier, find_colors
from .sound import sound_with_path
from .mr_anki_db_client import AnkiDbClient

class NoteMaker:
    def __init__(self, dictionary, external_media_path, anki_db_file_path, target_note_type=None, note_target_maps={}, emitter=None, thread_obj=None):
        self.emitter = emitter
        self.thread_obj = thread_obj
        self.dictionary = dictionary
        self.external_media_path = external_media_path
        self.target_note_type = target_note_type
        self.anki_db_file_path = anki_db_file_path

        # do this defaulting here in case they explicitly pass None, which would override argument default
        if self.target_note_type == None:
            self.target_note_type = 'defaultScannerModel'

        self.note_target_maps = note_target_maps

        # this is the list of fields that can be generated to offer to the UI
        self.generated_fields = {
            'word': '<b>Word</b><br>The word as scanned, could be traditional or simplified',
            'simp': '<b>Simplified</b><br>The scanned word forced into simplified characters',
            'trad': '<b>Traditional</b><br>The scanned word forced into traditional characters',
            'color_pinyin': '<b>Pin Yin</b><br>Pin Yin of the scanned word with tone colors applied',
            'sound': '<b>Sound</b><br>Sound file of the scanned word',
            'definition': '<b>Definition</b><br>English definition of the scanned word',
            'classifier': '<b>Classifier</b><br>The classifier used to count the scanned word if its a noun',
            'color_word': '<b>Color</b><br>The scanned word with tone colors applied to the characters',
            'sentence': '<b>Sentence</b><br>The phrase or sentence where the scanned word was first found',
            'sentence_color_pinyin': '<b>Sentence Pin Yin</b><br>Pin Yin of the sentence with tone colors applied',
            'sort_order': '<b>Sort</b><br>The index where the word was first found',
            'frequency': '<b>Frequency</b><br>The global frequency of the word as reported by the dictionary'
        }

        self.default_model = genanki.Model(
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

    def set_note_model(self):
        if self.target_note_type == 'defaultScannerModel':
            self.note_model = self.default_model
        else:
            self.target_model = self.existing_models[self.target_note_type]

            self.note_model = genanki.Model(
                self.target_note_type,
                self.target_model['name'],
                fields = self.target_model['flds'],
                templates = self.target_model['tmpls'],
                css = self.target_model['css']
            )

    def get_anki_note_models(self):
        ''' the models look like this:
            guid:
                name: 'name'
                flds: [{name:'field1'},{},{}..]
                tmpls: [{name:'card1'},{},{}..]
                css: ''
        '''
        self.existing_models = {}
        self.existing_models['defaultScannerModel'] = {
            'name': 'Default scanner model',
            'flds': [{'name':'Using default settings'}]
        }

        with AnkiDbClient(self.anki_db_file_path, self.printOrLog) as dbClient:
            noteModels = dbClient.get_anki_note_models()

        self.existing_models.update(noteModels)
        return self.existing_models

    def display_existing_node_models(self):
        if self.existing_models != None:
            for item in self.existing_models:
                self.printOrLog(f"\n\nNote model: {item}")
                self.printOrLog(f"Name: {self.existing_models[item]['name']}\nfields:")
                for field in self.existing_models[item]['flds']:
                    self.printOrLog(f"    {field['name']}")
                self.printOrLog(f"cards:")
                for card in self.existing_models[item]['tmpls']:
                    self.printOrLog(f"    {card['name']}")
        else:
            self.printOrLog(f"No existing models {self.existing_models}")

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
        #res = [rawNote.word, simp, trad, color_pinyin, sound, definition,
        #        classifier, color, rawNote.sentence, sentence_color_pinyin,
        #        str(rawNote.sort_order), frequency]

        mr_result = {
            'word': rawNote.word,
            'simp': simp,
            'trad': trad,
            'color_pinyin': color_pinyin,
            'sound': sound,
            'definition': definition,
            'classifier': classifier,
            'color_word': color,
            'sentence': rawNote.sentence,
            'sentence_color_pinyin': sentence_color_pinyin,
            'sort_order': str(rawNote.sort_order),
            'frequency': frequency
        }

        res = []
        if self.target_note_type == 'defaultScannerModel':
            for target in mr_result:
                res.append(mr_result[target])
        else:
            assert len(self.note_model.fields) > 1

            target_map = self.note_target_maps[self.target_note_type]
            reversed_map = {}
            for item in target_map:
                val = target_map[item]
                reversed_map[val] = item

            for target in self.target_model['flds']:
                t = reversed_map.get(target['name'])
                if t != None:
                    d = mr_result[t]
                else:
                    d = ''
                res.append(d)

            assert len(res) == len(self.note_model.fields)

        return res, join(dirname(realpath(__file__)),self.external_media_path,media_path)

    # @param rawNoteDict should be a dictionary of ChineseNote objects from ./mr_text_scanner.py
    def make_notes(self, rawNoteDict, deck_name, out_path, tag, include_sound=False):
        deck = genanki.Deck(
            2051337110,
            deck_name
        )

        self.get_anki_note_models()

        if self.existing_models != None and self.target_note_type != None and self.existing_models.get(self.target_note_type) != None and (self.note_target_maps.get(self.target_note_type) != None or self.target_note_type == 'defaultScannerModel'):
            if self.target_note_type == 'defaultScannerModel':
                self.printOrLog("\nPreparing new words using the default note model. You can configure which of your existing note models will be used from scanner menu on the anki main window.")
            else:
                self.printOrLog(f"\nPreparing new words using using the {self.existing_models[self.target_note_type]['name']} note model")

            self.set_note_model()
            self.printOrLog("\nNow gathering enrichment data for the words, this may take a while, especially if you are including audio files. The scanner will update progress here every 25 words...")
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

            try:
                #apkg.write_to_file(out_path)
                #self.printOrLog(f"Note maker wrote {len(rawNoteDict)} new notes to to {join(dirname(realpath(__file__)),out_path)}")
                #self.printOrLog(f"You can now import your apkg file to anki.")
                return apkg
            except:
                e = traceback.format_exc()
                self.printOrLog("\nThe note maker encountered an error. Please make sure that your output path is in an existing directory (case sensitive)")
                self.printOrLog(f"\nError: {e}")
        else:
            self.printOrLog("\nPlease configure the target note type first. You can find the option in the text scanner menu on the anki main window.")
