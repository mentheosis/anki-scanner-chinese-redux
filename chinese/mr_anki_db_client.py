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
    ## just a debugging method to explore anki file
    def query_db(self, query):
        try:
            db_path = self.anki_db_file_path
            conn = connect(db_path)
            c = conn.cursor()
        except:
            self.printOrLog("Could not open your anki collection, try changing the anki_db_path in the config file of this addon.")
            return {}

        query = query.strip()
        input_query = ''
        if query == 'master':
            input_query = 'master'
            query = 'select * from sqlite_master'
        elif query == 'models':
            input_query = 'models'
            query = 'select models from col'

        self.printOrLog(f"query {query}")
        try:
            c.execute(query)
            rowct = 1
            for row in c:
                if input_query == 'select * from sqlite_master':
                    self.printOrLog(f"\n\nrow {rowct}\n {row[0]}, {row[1]}, {row[2]}, {row[3]}")
                    sub_row = row[4].split("\n")
                    for sub in sub_row:
                        self.printOrLog(sub)

                elif input_query == 'models':
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
