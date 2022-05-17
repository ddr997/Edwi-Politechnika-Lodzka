# Cw.4 EDWI (24.05.22) Maciej Lukaszewicz 239550, SRiPM Informatyka
import os.path
import requests, re, csv, string, json
import nltk
import numpy as np
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
                text = localCrawl.removeTagsFromHtml()
                nGram = self.createNGram(self.tokenize(text), n)
                print(f"({i})Visiting and creating Ngram: {v}")
                Builder.append(nGram)
                self.writeToJSON(v, text, nGram)
            except:
                print(f"({i})--  Ngrams creation failed, ignoring this site {v}  --")
                errors.append(i)
                continue
        for i in errors:
            self.URLS.pop(i)
        self.Ngrams = Builder
        return Builder

    def writeToJSON(self, URL, content, Ngram):
        toSave = {"content": content, "Ngram": Ngram}
        if not os.path.isfile('sites.json'):
            with open('sites.json', "w") as begin:
                begin.write("{}")

        with open('sites.json', 'r', encoding="utf8") as fileReader:
            file = json.load(fileReader)
            file[URL] = toSave

        with open('sites.json', 'w', encoding="utf8") as fileWriter:
            json.dump(file, fileWriter, indent=2, ensure_ascii=False)
            print("Adding site to JSON database.")

    def calculateJaccardIndex(set1: list, set2: list):
        if set1 and set2:
            commonElements = list(set(set1).intersection(set2))
            output = len(commonElements)/(len(set(set1))+len(set(set2))-len(commonElements))
        else:
            return -1
        return np.round(output, 6)

    def calculateCosineDistance(set1: list, set2: list):
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

    def createJaccardIndexRanking():
        with open("sites.json", 'r', encoding = "utf8") as file:
            database = json.load(file)
        length = len(database)
        jaccardMatrix = np.zeros((length, length))
        for i, A in enumerate(database):
            for j, B in enumerate(database):
                jaccardMatrix[i, j] = Crawler.calculateJaccardIndex(database[A]["Ngram"], database[B]["Ngram"])
        return np.round(jaccardMatrix, 3)

    def createCosineDistanceRanking():
        with open("sites.json", 'r', encoding = "utf8") as file:
            database = json.load(file)
        length = len(database)
        cosineMatrix = np.zeros((length, length))
        for i, A in enumerate(database):
            for j, B in enumerate(database):
                cosineMatrix[i, j] = Crawler.calculateCosineDistance(database[A]["Ngram"], database[B]["Ngram"])
        return np.round(cosineMatrix, 3)

    def askForSimilarDocument(URL, n):
        site = Crawler(URL)
        tokens = site.tokenize(site.removeTagsFromHtml())
        nGram = site.createNGram(tokens, n)

        try:
            with open('sites.json', 'r', encoding="utf8") as fileReader:
                database = json.load(fileReader)
        except:
            raise FileNotFoundError("Database not found.")

        test = database[list(database.keys())[0]]["Ngram"][0]
        l = len(test.split(" "))
        if l != n:
            raise ValueError(f"Ngrams in database are differ with declared n, please update your database.(nArgumentu = {n}, nBazy = {l})")
            # Crawler().createNgrams(n)
            # try:
            #     with open('sites.json', 'r', encoding="utf8") as fileReader:
            #         database = json.load(fileReader)
            # except:
            #     raise FileNotFoundError("Database not found.")

        cosineSimilarity = {}
        jaccardSimilarity = {}
        for i in database:
            cosineVal = Crawler.calculateCosineDistance(nGram, database[i]["Ngram"])
            jaccardVal = Crawler.calculateJaccardIndex(nGram, database[i]["Ngram"])
            cosineSimilarity[i] = cosineVal
            jaccardSimilarity[i] = jaccardVal
        print("Cosine dict:\n", cosineSimilarity)
        print("Jaccard dict:\n", jaccardSimilarity)
        print("Cosine values: ", cosineSimilarity.values())
        print("Jaccard values: ", jaccardSimilarity.values())
        print("Top 3 values of cosine:\n ", Counter(cosineSimilarity).most_common(3))
        print("Top 3 values of jaccard:\n", Counter(jaccardSimilarity).most_common(3))


if __name__ == "__main__":
    # np.set_printoptions(threshold=np.inf)
    URL = input("Enter the URL for generating database (press Enter for default): ") or \
          "https://en.wikipedia.org/wiki/Wykop.pl"
    crawler = Crawler(URL)
    crawler.createNgrams(2)

    URL = input("Enter the URL for similarity check (press Enter for default): ") or \
          'http://www.wykop.pl/ludzie/lechwalesa/'
    Crawler.askForSimilarDocument(URL, 2)
