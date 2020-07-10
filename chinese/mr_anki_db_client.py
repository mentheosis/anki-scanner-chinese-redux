import os, json, traceback
from os.path import dirname, join, realpath
from sqlite3 import connect

class AnkiDbClient:
    def __init__(self, anki_db_file_path, emitterFn=None):
        self.anki_db_file_path = anki_db_file_path
        self.emitterFn = emitterFn

    def __enter__(self):
        try:
            db_path = self.anki_db_file_path
            self.conn = connect(db_path)
            return self
        except:
            self.printOrLog("Could not open your anki collection, try changing the anki_db_path in the config file of this addon.")

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()

    def printOrLog(self, message):
        if self.emitterFn != None:
            self.emitterFn(message)
        else:
            print(message)


    def get_anki_note_models(self):
        c = self.conn.cursor()
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
        This will look in the first two positions of a note for the given field key.
        If found it will return all the card ids that go with that note.
        It takes an array of keys to search for
    '''
    def get_card_ids(self, keys):
        c = self.conn.cursor()

        whereClause = "("
        for key in keys:
            whereClause = whereClause+f"'{key}',"
        # trim off the last comma
        whereClause = whereClause[:-1]
        whereClause = whereClause+")"

        query = "select c.id from cards c"+ \
        " join notes n on n.id = c.nid"+ \
        f" where c.queue <> -1 and (substr(flds, 0, instr(flds,char(31))) in {whereClause}"+ \
        " or substr(substr(flds, instr(flds,char(31))+1), 0,"+ \
        f" instr(substr(flds, instr(flds,char(31))+1),char(31))) in {whereClause})"

        try:
            c.execute(query)
            result = []
            for row in c:
                result.append(row[0])
            return result
        except:
            e = traceback.format_exc()
            self.printOrLog(f"\nError: {e}")

    '''
        Mirrors the anki api call "mw.col.getCard" except handles a batch of ids at once
    '''
    def get_cards_by_ids(self, ids):
        c = self.conn.cursor()

        whereClause = "("
        for id in ids:
            whereClause = whereClause+f"'{id}',"
        if len(ids) > 0:
            # trim off the last comma
            whereClause = whereClause[:-1]
        whereClause = whereClause+")"

        query = "select data,did,due,factor,flags,id,ivl,lapses,left,mod,nid,odid,odue,ord,queue,reps,type,usn "+ \
        f"from cards where id in {whereClause}"

        try:
            c.execute(query)
            result = []
            for row in c:
                d = {'data': row[0],
                    'did': row[1],
                    'due': row[2],
                    'factor': row[3],
                    'flags': row[4],
                    'id': row[5],
                    'ivl': row[6],
                    'lapses': row[7],
                    'left': row[8],
                    'mod': row[9],
                    'nid': row[10],
                    'odid': row[11],
                    'odue': row[12],
                    'ord': row[13],
                    'queue': row[14],
                    'reps': row[15],
                    'type': row[16],
                    'usn': row[17]
                }
                result.append(d)
            return result
        except:
            e = traceback.format_exc()
            self.printOrLog(f"\nError: {e}")



    '''
    ################ below this point are kinda silly dev debug functions

    # sql lite schema for reference
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
        c = self.conn.cursor()
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


    ## just a debugging method to explore anki file
    def query_db(self, query):
        c = self.conn.cursor()

        query = query.strip()
        input_query = self.transform_query_convenience_shortcuts(query)
        self.printOrLog(f"query {query}")

        try:
            c.execute(input_query)
            rowct = 1
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
