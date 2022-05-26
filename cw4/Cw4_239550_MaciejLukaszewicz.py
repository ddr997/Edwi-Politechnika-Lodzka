# Cw.3 EDWI (17.05.22) Maciej Lukaszewicz 239550, SRiPM Informatyka
import math
import os.path
import sys
import time
from tqdm import tqdm

import requests, re, csv, string, json
import nltk
import numpy as np
from collections import Counter
from nltk.stem import PorterStemmer
from urllib.parse import urlparse
np.set_printoptions(threshold=sys.maxsize)

class Crawler:

    extensionsToIgnore = [".js", ".css", ".png", ".jpg", ".pdf", ".jpeg", ".ico", ".webp", ".woff", ".woff2", ".svg"]

    def __init__(self, initialURL):
        self.initialURL = initialURL
        self.URLS = []
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36', }
            self.requestResponse = requests.get(self.initialURL, headers=headers, timeout=3)
            self.requestResponse.encoding = 'utf-8'
            self.textWithHtmlTags = self.requestResponse.text
            if self.requestResponse.status_code != 200:
                raise Exception("-- Status code different than 200, skipping this site! --")
        except:
            raise ConnectionError("Provided invalid URL address or cannot connect to the page (check connection).")

    def removeTagsFromHtml(self):
        regex = r'<(script|style).*>(.|\n)*?</(script|style)>|<[^>]*>'
        tagsRemoved = re.sub(regex, "", self.textWithHtmlTags)
        newlinesRemoved = tagsRemoved.replace("\n", " ")
        whitespacesRemoved = re.sub(r"\s{2,}", " ", newlinesRemoved)
        filteredText = whitespacesRemoved
        return filteredText

    def getUrls(self):
        regexForURL = r'(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]+\.[a-zA-Z0-9()]+\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*))'
        urlsFound = list(set(re.findall(regexForURL, self.textWithHtmlTags)))
        urlsFound = [i for i in urlsFound if not any(j in i for j in Crawler.extensionsToIgnore)]  # ext. ignore
        urlsFound = list(set([re.sub("https", "http", i) for i in urlsFound])) # filtr prefixow http
        self.URLS = urlsFound
        return urlsFound

    @staticmethod
    def tokenize(textToFilter):
        tokens = nltk.tokenize.word_tokenize(textToFilter)
        noPunctuation = [t for t in tokens if t not in string.punctuation] # filtr znakow
        pattern = re.compile(r"\b[^\d\W]+\b")
        noDigits = [t for t in noPunctuation if pattern.match(t)]
        ps = PorterStemmer()
        stemmed = [ps.stem(token) for token in noDigits]
        return stemmed

    @staticmethod
    def readFromJSON(filename: str) -> dict:
        try:
            with open(filename, 'r', encoding="utf8") as fileReader:
                file = json.load(fileReader)
                return file
        except:
            return {}

    @staticmethod
    def writeToJSON(filename, records):
        if not os.path.isfile(filename):
            with open(filename, "w") as begin:
                begin.write("{}")

        file = Crawler.readFromJSON(filename)
        file = file | records

        with open(filename, 'w', encoding="utf8") as fileWriter:
            json.dump(file, fileWriter, ensure_ascii=False)


    def createDatabase(self, depth: int, filename: str):
        urlsToVisit = self.getUrls()
        database = Crawler.readFromJSON(filename)
        databaseURLS = [i["URL"] for i in database.values()]
        amountOfRecords = len(databaseURLS)
        domain = urlparse(self.initialURL).netloc
        currentIndex = amountOfRecords+1
        while currentIndex <= amountOfRecords+depth:
            url = urlsToVisit.pop(0)
            if url in databaseURLS:
                continue
            try:
                localCrawl = Crawler(url)

                if len(urlsToVisit) < 2*depth:  # dla pewności crawlingu utrzymujemy x2 wiecej url niz depth
                    urlsToVisit.extend(localCrawl.getUrls())

                textToSave = localCrawl.removeTagsFromHtml()
                database.update({currentIndex:{"URL":url, "Category":domain, "Content": textToSave}})
                print(f"({currentIndex})Crawling successful: {url}")
                currentIndex += 1

            except ValueError as ve: # status code error
                print(f"({currentIndex})" + ve.args[0] + ": " + url)
                urlsToVisit.pop(0)
                continue
            except ConnectionError as ce:
                print(f"({currentIndex})" + ce.args[0] + ": " + url)
                urlsToVisit.pop(0)
                continue

        Crawler.writeToJSON(filename, database)
        print("*** Added crawled sites to the database ***\n")
        return 0

    @staticmethod
    def bagOfWords(filename) -> Counter:
        bag = {}
        database = Crawler.readFromJSON("sites.json")
        for index in tqdm(database):
            text = database[index]["Content"]
            tokens = set(Crawler.tokenize(text))
            for word in tokens:
                if word in bag:
                    bag[word] += 1
                else:
                    bag[word] = 1
        Crawler.writeToJSON("bow.json", bag)
        print("*** Saved Bag of Words to json ***\n")
        return bag

    @staticmethod
    def getSingleBow(index: int):
        bagOfWords = list(Crawler.readFromJSON("bow.json"))
        content = Crawler.readFromJSON("sites.json")[str(index)]["Content"]
        tokens = Crawler.tokenize(content)

        counter = Counter(tokens)
        emptyBow = [0]*len(bagOfWords)
        for word in counter:
            indexInBag = bagOfWords.index(word)
            count = counter.get(word)
            emptyBow[indexInBag] = count
        bow = emptyBow
        return bow

    @staticmethod
    def extendDatabaseWithBows(filename):
        database = Crawler.readFromJSON(filename)
        for i in tqdm(database.keys()):
            bow = Crawler.getSingleBow(i)
            database[i]["bow"] = bow
        Crawler.writeToJSON(filename, database)
        print("*** Database extended with Bows ***\n")

    @staticmethod
    def calculateTF_IDF(index: int):
        database = Crawler.readFromJSON("sites.json")
        content = database[str(index)]["Content"]
        tokens = Crawler.tokenize(content)

        counter = Counter(tokens)
        words = list(counter.keys())

        # tf
        counter = Counter(tokens)
        amountOfWords = sum(counter.values())
        tf = [counter.get(i)/amountOfWords for i in words]

        # idf
        documentsAmount = len(database.values())
        bagOfWords = Crawler.readFromJSON("bow.json")
        idf = [math.log10(documentsAmount/bagOfWords.get(i)) for i in words]

        # tf_idf
        tf_idf = {words[i] : np.round(tf[i]*idf[i], 7) for i in range(0, len(words))}
        emptyVector = [0] * len(bagOfWords)
        wordsInBag = list(bagOfWords.keys())

        for word in tf_idf.keys():
            indexInBag = wordsInBag.index(word)
            value = tf_idf.get(word)
            emptyVector[indexInBag] = value
        vector = emptyVector
        return vector

    @staticmethod
    def extendDatabaseWithTF_IDF(filename):
        database = Crawler.readFromJSON(filename)
        for i in tqdm(database.keys()):
            tf_idf = Crawler.calculateTF_IDF(i)
            database[i]["TF_IDF"] = tf_idf
        Crawler.writeToJSON(filename, database)
        print("*** Database extended with tf-idf ***\n")


    @staticmethod
    def askForSimilarDocument(self, URL):
        site = Crawler(URL)
        tokens = site.tokenize(site.removeTagsFromHtml())


if __name__ == "__main__":

    baseSites = ["https://www.theguardian.com/world", "https://www.techradar.com/",
                 "https://www.pcworld.com/", "https://www.nytimes.com/international/section/sports",
                 "https://www.pcgamer.com/news/"]

    for i in baseSites:
        print("*** Starting with site: *** " + i)
        crawler = Crawler(i)
        crawler.createDatabase(100, "sites.json")

    Crawler.bagOfWords("sites.json")
    Crawler.extendDatabaseWithBows("sites.json")
    Crawler.extendDatabaseWithTF_IDF("sites.json")