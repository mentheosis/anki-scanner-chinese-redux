
from .mr_anki_db_client import AnkiDbClient
import jieba
import time

from aqt import mw

class TextReader:

    def dedupe(self, list):
        deduped = []
        count=0
        for item in list:
            count += 1
            if not item in deduped:
                deduped.append(item)
        return deduped, count

    def __init__(self, logFn=None):
        self.log = logFn

    '''
        text is meant to be something that the user has just finished reading.
        missed words is the csv list of words that they had to look up while reading.
        any words parsed from the text that arent in the missed list will be counted as a successful flashcard answer
    '''
    def readText(self, text, missedWords, anki_db_file_path):
        self.log(f"Reader starting")

        with AnkiDbClient(anki_db_file_path, self.log) as dbClient:
            missedWordsRaw, missedCount = self.dedupe(missedWords.split(","))
            self.missedWords = []
            missedIds = []
            if len(missedWordsRaw) > 0:
                missedIds = dbClient.get_card_ids(missedWordsRaw)
            if len(missedIds) > 0:
                self.missedWords = dbClient.get_cards_by_ids(missedIds)

            learnedWordsRaw, learnedWordsCount = self.dedupe(jieba.cut(text, cut_all=False))
            ids = []
            learnedIds = []
            self.learnedWords = []
            if len(learnedWordsRaw) > 0:
                ids = dbClient.get_card_ids(learnedWordsRaw)
                learnedIds = [id for id in ids if id not in missedIds]
            if len(learnedIds) > 0:
                self.learnedWords = dbClient.get_cards_by_ids(learnedIds)

        self.log(f"\nTotal input words: {learnedWordsCount} \nDistinct input words: {len(learnedWordsRaw)}")
        self.log(self.printReportShort())
        self.log(f"\nFinished reading. Click 'Update my cards' to set responses in the anki scheduler")

    def answerCards(self):
        learnedCount = 0
        missedCount = 0
        for card in self.learnedWords:
            learnedCount = learnedCount + 1
            card.timerStarted = time.time()
            card.queue = 2
            mw.col.sched.answerCard(card, 3)
        for card in self.missedWords:
            missedCount = missedCount + 1
            card.timerStarted = time.time()
            card.queue = 2
            mw.col.sched.answerCard(card, 1)
        return (learnedCount, missedCount)

        return True


    def printReportShort(self):
        outputString = f"Cards to pass: {len(self.learnedWords)}"
        outputString = outputString + f"\nCards to miss: {len(self.missedWords)}"
        return outputString

    def printReport(self):
        outputString = "learned words: "
        for word in self.learnedWords:
            note = word.note()
            outputString = outputString + "("
            for (name, value) in note.items():
                if name == "Hanzi" or name == "Simplified" or name == "Traditional":
                    outputString = outputString + value + ","
            outputString = outputString +"),"
        outputString = outputString + "missed words: "
        for word in self.missedWords:
            note = word.note()
            outputString = outputString + "("
            for (name, value) in note.items():
                if name == "Hanzi" or name == "Simplified" or name == "Traditional":
                    outputString = outputString + value + ","
            outputString = outputString +"),"
        outputString = f"\nCards passed: {len(self.learnedWords)}"
        outputString = outputString + f"\nCards missed: {len(self.missedWords)}"
        return outputString
