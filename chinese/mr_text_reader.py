from aqt import mw
import jieba
import time

class TextReader:
    def dedupe(self, list):
        deduped = []
        for item in list:
            if not item in deduped:
                deduped.append(item)
        return deduped

    def __init__(self, logFn=None):
        self.log = logFn

    '''
        text is meant to be something that the user has just finished reading.
        missed words is the csv list of words that they had to look up while reading.
        any words parsed from the text that arent in the missed list will be counted as a successful flashcard answer
    '''
    def readText(self, text, missedWords):
        missedWords = missedWords.split(",")
        missedIds = []
        for word in missedWords:
            missedIds.extend(self.findIdsForHanzi(word))
        self.log("Reader finished finding ids for missedWords")
        missedIds = self.dedupe(missedIds)

        learnedWordsRaw = jieba.cut(text, cut_all=False)
        learnedIds = []
        for word in learnedWordsRaw:
            ids = self.findIdsForHanzi(word)
            ids = [id for id in ids if id not in missedIds]
            learnedIds.extend(ids)
        learnedIds = self.dedupe(learnedIds)
        self.log("Reader finished finding ids for learnedWordsRaw")

        self.learnedWords = []
        for id in learnedIds:
            self.learnedWords.append(mw.col.getCard(id))
        self.log("Reader finished learnedWords loop")

        self.missedWords = []
        for id in missedIds:
            self.missedWords.append(mw.col.getCard(id));
        self.log("Reader finished missedWords loops")

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
        return outputString

    def findIdsForHanzi(self, hanzi):
        ids = self.findIdsWithTag(hanzi, "Hanzi")
        ids.extend(self.findIdsWithTag(hanzi, "Simplified"))
        ids.extend(self.findIdsWithTag(hanzi, "Traditional"))
        dedupedIds = []
        for id in ids:
            if not id in dedupedIds:
                dedupedIds.append(id)
        return dedupedIds

    def findIdsWithTag(self, hanzi, tag):
        return mw.col.findCards(tag+":"+hanzi)
