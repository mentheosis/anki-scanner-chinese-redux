import os, json, traceback
from os.path import dirname, join, realpath
from sqlite3 import connect

class AnkiDbClient:
    def __init__(self, anki_db_file_path, emitterFn=None):
        self.anki_db_file_path = anki_db_file_path
        self.emitterFn = emitterFn

    def printOrLog(self, message):
        if self.emitterFn != None:
            self.emitterFn(message)
        else:
            print(message)


    def get_anki_note_models(self):
        try:
            db_path = self.anki_db_file_path
            conn = connect(db_path)
            c = conn.cursor()
        except:
            self.printOrLog("Could not open your anki collection, try changing the anki_db_path in the config file of this addon.")
            return {}

        query = 'select models from col'
        try:
            c.execute(query)
            # seems that Anki stores the notes as a single row in this table
            row = next(c)
            j = json.loads(row[0])
            return j
        except:
            e = traceback.format_exc()
            self.printOrLog(f"\nError: {e}")


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

    # this provides some easy access to commonly useful queries in a shorthand way
    # its not discoverable but its handy if you know to use it.
    def transform_query_convenience_shortcuts(self, query):
        if query == 'master':
            return 'select * from sqlite_master'
        elif query == 'models':
            return 'select models from col'
        elif query[0:9] == 'show tag ':
            tag = query[9:]
            return f"select flds from notes where tags like '%{tag}%'"
        else:
            return query


    def show_words_with_tag(self, query, dictionary, anki_note_indices):
        c = self.prep_connection()
        query = query.strip()
        input_query = self.transform_query_convenience_shortcuts(query)
        try:
            c.execute(input_query)
            found_words = {}
            for row in c:
                note_fields = row[0].split("\x1f")
                for idx in anki_note_indices:
                    word = note_fields[idx]
                    simp = dictionary._get_word(word[0],"simp")
                    if simp != None and found_words.get(word) == None:
                        found_words[word] = word
                        self.printOrLog(f"{word}，")
        except:
            e = traceback.format_exc()
            self.printOrLog(f"\nError: {e}")


    def prep_connection(self):
        try:
            db_path = self.anki_db_file_path
            conn = connect(db_path)
            c = conn.cursor()
        except:
            self.printOrLog("Could not open your anki collection, try changing the anki_db_path in the config file of this addon.")
            return False

        return c

    ## just a debugging method to explore anki file
    def query_db(self, query):
        c = self.prep_connection()

        query = query.strip()
        input_query = self.transform_query_convenience_shortcuts(query)
        self.printOrLog(f"query {query}")

        try:
            c.execute(input_query)
            rowct = 1
            if query[0:9] == 'show tag ':
                self.show_words_with_tag(c)
            else:
                for row in c:
                    if input_query == 'select * from sqlite_master':
                        self.printOrLog(f"\n\nrow {rowct}\n {row[0]}, {row[1]}, {row[2]}, {row[3]}")
                        sub_row = row[4].split("\n")
                        for sub in sub_row:
                            self.printOrLog(sub)

                    elif query == 'models':
                        j = json.loads(row[0])
                        for item in j:
                            self.printOrLog(f"\n\nNote model: {item}")
                            self.printOrLog(f"Name: {j[item]['name']}\nfields:")
                            for field in j[item]['flds']:
                                self.printOrLog(f"    {field['name']}")
                            self.printOrLog(f"cards:")
                            for card in j[item]['tmpls']:
                                self.printOrLog(f"    {card['name']}")

                    elif type(row) is tuple:
                        self.printOrLog(f"\n\nrow {rowct}")
                        for field in row:
                            if type(field) == str and len(field) > 100:
                                try:
                                    j = json.loads(field)
                                    self.printOrLog(json.dumps(j,indent=2))
                                except:
                                    self.printOrLog(field)
                            else:
                                self.printOrLog(f"{field}")

                    else:
                        self.printOrLog(f"\n\nrow {rowct}\n {row}")
                    rowct += 1
        except:
            e = traceback.format_exc()
            self.printOrLog(f"\nError: {e}")
