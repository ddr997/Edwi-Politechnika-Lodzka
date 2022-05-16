# Cw.2 EDWI (10.05.22) Maciej Lukaszewicz 239550, SRiPM Informatyka
import os.path

import requests, re, csv, string, json
import nltk
import numpy as np
from pathlib import Path
from collections import Counter
from nltk.stem import PorterStemmer


class Crawler:
    extensionsToIgnore = [".js", ".css", ".png", ".jpg", ".pdf", ".jpeg", ".ico"]
    def __init__(self, initialURL):
        self.initialURL = initialURL
        self.URLS = []
        self.Ngrams = []
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36', }
            self.requestResponse = requests.get(self.initialURL, headers=headers)
            self.requestResponse.encoding = 'utf-8'
            self.textWithHtmlTags = self.requestResponse.text
        except:
            raise ValueError("Provided invalid URL address or cannot connect to the page (check internet).")

    def removeTagsFromHtml(self):
        regex = r'<(script|style).*>(.|\n)*?</(script|style)>|<[^>]*>'
        tagsRemoved = re.sub(regex, "", self.textWithHtmlTags)
        whitespacesRemoved = re.sub(r"\s{2,}", "\n", tagsRemoved)
        filteredText = whitespacesRemoved
        return filteredText

    def getUrls(self):
        regexForURL = r'(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]+\.[a-zA-Z0-9()]+\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*))'
        urlsFound = list(set(re.findall(regexForURL, self.textWithHtmlTags)))
        urlsFound = [i for i in urlsFound if not any(j in i for j in Crawler.extensionsToIgnore)]  # ext. ignore
        urlsFound = list(set([re.sub("https", "http", i) for i in urlsFound])) # filtr prefixow http
        print("URLS on the main page: ", urlsFound)
        self.URLS = urlsFound
        return urlsFound

    def writeToCsv(self, item, filename):
        with open(f'{filename}.csv', 'w+', encoding="utf-8", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(item)

    def crawlAndSaveToFiles(self):
        urlsToVisit = self.getUrls()
        initEmails = self.getEmails()
        initText = self.removeTags()
        listOfText = [[self.initialURL, initText]]
        listOfEmails = [[self.initialURL, initEmails]]

        for url in urlsToVisit:
            print("\nEntering URL: ", url)
            try:
                localInstance = Crawler(url)
            except:
                continue
            listOfText.append([url, localInstance.removeTags()])
            listOfEmails.append([url, localInstance.getEmails()])

    def tokenize(self, textToFilter):
        tokens = nltk.tokenize.word_tokenize(textToFilter)
        noPunctuation = [t for t in tokens if t not in string.punctuation] # filtr znakow
        pattern = re.compile(r"\b[^\d\W]+\b")
        noDigits = [t for t in noPunctuation if pattern.match(t)]
        ps = PorterStemmer()
        stemmed = [ps.stem(token) for token in noDigits]
        return stemmed

    def createNGram(self, tokens: list, n: int):
        length = len(tokens)
        Ngrams = []
        for i in range(0, length-n+1):
            Ngrams.append(
                " ".join(
                    tokens[i:i+n]
                )
            )
        return Ngrams

    def createNgrams(self, n: int):
        urlsToVisit = self.getUrls()
        Builder = []
        errors = []
        for i, v in enumerate(urlsToVisit):
            try:
                localCrawl = Crawler(v)
                print(f"({i})Visiting and creating Ngram: {v}")
                Builder.append(
                    localCrawl.createNGram(
                        self.tokenize(
                            localCrawl.removeTagsFromHtml()
                        )
                    , n)
                )
            except:
                print(f"({i})--  Ngrams creation failed, ignoring this site {v}  --")
                errors.append(i)
                continue
        for i in errors:
            self.URLS.pop(i)
        self.Ngrams = Builder
        return Builder

    def calculateJaccardIndex(self, set1, set2):
        if set1 and set2:
            commonElements = list(set(set1).intersection(set2))
            output = len(commonElements)/(len(set(set1))+len(set(set2))-len(commonElements))
        else:
            return -1
        return np.round(output, 6)

    def calculateCosineDistance(self, set1: list, set2: list):
        if set1 and set2:
            bagOfWords = list(set(
                set1 + set2
            ))
            vec1 = np.asarray([0]*len(bagOfWords))
            vec2 = np.asarray([0]*len(bagOfWords))
            for i,v in enumerate(bagOfWords):
                if v in set1:
                    vec1[i] = 1
                if v in set2:
                    vec2[i] = 1
            numerator = np.einsum('i,i',vec1, vec2)
            # dist = np.linalg.norm(vec1) * np.linalg.norm(vec2)
            dist = np.sqrt(vec1.dot(vec1)) * np.sqrt(vec2.dot(vec2))
            cosine = numerator/dist
            return np.round(cosine, 6)
        else:
            return -1

    def createJaccardIndexRanking(self):
        length = len(self.URLS)
        jaccardMatrix = np.zeros((length, length))
        for i, A in enumerate(self.Ngrams):
            for j, B in enumerate(self.Ngrams):
                jaccardMatrix[i,j] = self.calculateJaccardIndex(A,B)
        return jaccardMatrix

    def createCosineDistanceRanking(self):
        length = len(self.URLS)
        cosineMatrix = np.zeros((length, length))
        for i, A in enumerate(self.Ngrams):
            for j, B in enumerate(self.Ngrams):
                cosineMatrix[i,j] = self.calculateCosineDistance(A,B)
        return cosineMatrix

    def askForSimilarDocument(self, URL, n):
        site = Crawler(URL)
        tokens = site.tokenize(site.removeTagsFromHtml())
        nGram = site.createNGram(tokens, n)
        cosineSimilarity = []
        jaccardSimilarity = []
        self.createNgrams(n)
        for i in self.Ngrams:
            cosineSimilarity.append(self.calculateCosineDistance(nGram, i))
            jaccardSimilarity.append(self.calculateJaccardIndex(nGram, i))
        print(cosineSimilarity)
        print(jaccardSimilarity)


    def writeToJSON(self, URL, content, Ngram):
        toSave = {"content": content, "Ngram": Ngram}
        file = None

        if not os.path.isfile('sites.json'):
            with open('sites.json', "w") as begin:
                begin.write("{}")

        with open('sites.json', 'r') as fileReader:
            file = json.load(fileReader)
            file[URL] = toSave

        with open('sites.json', 'w') as fileWriter:
            json.dump(file, fileWriter, indent=2)
            print("The json file is created")


if __name__ == "__main__":
    np.set_printoptions(threshold=np.inf)
    URL = input("Enter the URL (press Enter for default): ") or "https://en.wikipedia.org/wiki/Wykop.pl"
    crawler = Crawler(URL)

    crawler.writeToJSON("http://test.pl", "to jest kebab", ["to jest", "jest kebab"])
    # crawler.createJSON("https://en.wikipedia.org/wiki/Wykop.pl", "jebac psy policje", ["jebac psy", "psy policje"])
    # crawler.createJSON("https://en.wikipedia.org/wiki/Wykop", "jebac psy policje", ["jebac psy", "psy policje"])
    # crawler.askForSimilarDocument("https://dziennikbaltycki.pl/lech-walesa-spotkal-sie-z-internautami-portalu-wykoppl-zdjecia/ar/3343979", 4)

    # print(crawler.createJaccardIndexRanking())
    # print(crawler.createCosineDistanceRanking())
