# Cw.2 EDWI (10.05.22) Maciej Lukaszewicz 239550, SRiPM Informatyka

import requests, re, csv, string
import nltk
from collections import Counter
from nltk.stem import PorterStemmer


class Crawler:
    extensionsToIgnore = [".js", ".css", ".png", ".jpg", ".pdf", ".jpeg", ".ico"]
    def __init__(self, initialURL):
        self.initialURL = initialURL
        self.URLS = []
        self.invertedIndex = {}
        self.decodedInvertedIndex = []
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36', }
            self.requestResponse = requests.get(self.initialURL, headers=headers)
            self.requestResponse.encoding = 'utf-8'
            if self.requestResponse.status_code != 200:
                print("Status code different than 200, skipping page!\n")
                raise ValueError
            self.textWithHtmlTags = self.requestResponse.text
            self.initialInvertedIndexDict = self.getInvertedIndex(self.removeTagsFromHtml(), 0)
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

    def getEmails(self):
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emailsFound = " ".join(set(re.findall(regex, self.textWithHtmlTags)))
        print("Emails crawled from this page: ", emailsFound)
        return emailsFound

    def writeToCsv(self, item, filename):
        with open(f'{filename}.csv', 'w+', encoding="utf-8", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(item)

    def crawlAndSaveToFiles(self):
        urlsToVisit = self.getUrls()
        initEmails = self.getEmails()
        initText = self.removeTagsFromHtml()
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

    def getInvertedIndex(self, text, URL):
        tokens = self.tokenize(text)
        print(tokens)
        invertedIndexDict = {key.lower():[URL] for key in tokens}
        return invertedIndexDict

    def createInvertedIndex(self):
        urlsToVisit = self.getUrls()
        Builder = self.initialInvertedIndexDict
        for i, v in enumerate(urlsToVisit):
            try:
                localCrawl = Crawler(v)
                print(f"({i})Visiting and updating index: {v}")
                localDict = localCrawl.initialInvertedIndexDict
                for key in localDict:
                    if key in Builder.keys():
                        Builder[key].append(i)
                    else:
                        Builder[key] = [i]
            except:
                print(f"({i})--Crawling of this site failed: {v}--")
                continue

        self.invertedIndex = Builder
        self.decodedInvertedIndex = self.decodeIndex(Builder)
        print("--Created inverted index (also created file):\n", self.decodedInvertedIndex)
        self.writeToCsv([[i[0], " ".join(i[1])] for i in self.decodedInvertedIndex], "index")
        return Builder

    def decodeIndex(self, toDecode):
        return [[item, [self.URLS[index] for index in self.invertedIndex.get(item)]] for item in toDecode]

    def askForDocument(self, question: str):
        tokenizedQuestion = self.tokenize(question)
        print("Tokeny pytania: ", tokenizedQuestion)
        linksFound = []
        for word in tokenizedQuestion:
            try:
                linksFound.extend(self.invertedIndex[word])
            except:
                continue
        counter = Counter(linksFound)
        mostCommon = counter.most_common(8)
        print("Dokumenty pasujace do zapytania: ", mostCommon)
        for linkIndex in mostCommon:
            print(f"Count:({linkIndex[1]}) ", self.URLS[linkIndex[0]])


if __name__ == "__main__":
    URL = input("Enter the URL (press Enter for default): ") or "https://en.wikipedia.org/wiki/Wykop.pl"
    crawler = Crawler(URL)
    crawler.createInvertedIndex()
    question = input("Zadaj pytanie: ") or "wykop.pl Janusz Krzysztof AMA"
    crawler.askForDocument(question)
