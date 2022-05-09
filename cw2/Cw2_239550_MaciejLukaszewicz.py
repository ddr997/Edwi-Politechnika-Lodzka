# Cw.2 EDWI (8.04.22) Maciej Lukaszewicz 239550, SRiPM Informatyka
import string

import requests, re, csv
import nltk
from nltk.corpus import stopwords


class Crawler:
    extensionsToIgnore = [".js", ".css", ".png", ".jpg", ".pdf", ".jpeg", ".ico"]
    def __init__(self, initialURL):
        self.initialURL = initialURL
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36', }
            self.requestResponse = requests.get(self.initialURL, headers=headers)
            self.requestResponse.encoding = 'utf-8'
            self.textWithHtmlTags = self.requestResponse.text
            self.initialInvertedIndexDict = self.getInvertedIndex(self.removeTagsFromHtml(), self.initialURL)
        except:
            raise ValueError("Provided invalid URL address or cannot connect to the page (check internet).")

    def removeTagsFromHtml(self):
        regex = r'<(script|style).*>(.|\n)*?</(script|style)>|<[^>]*>'
        tagsRemoved = re.sub(regex, "", self.textWithHtmlTags)
        whitespacesRemoved = re.sub(r"\s{2,}", "\n", tagsRemoved)
        # noSpaceSplitter = re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ', whitespacesRemoved)
        # filteredText = noSpaceSplitter
        filteredText = whitespacesRemoved
        return filteredText

    def getUrls(self):
        regexForURL = r'(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]+\.[a-zA-Z0-9()]+\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*))'
        urlsFound = set(re.findall(regexForURL, self.textWithHtmlTags))
        urlsFound = {i for i in urlsFound if not any(j in i for j in Crawler.extensionsToIgnore)}  # ignore
        print("URLS on the main page: ", urlsFound)
        return urlsFound

    def getEmails(self):
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emailsFound = set(re.findall(regex, self.textWithHtmlTags))
        print("Emails crawled from this page: ", emailsFound)
        return emailsFound

    @staticmethod
    def writeToCsv(text, filename):
        with open(f'{filename}.csv', 'w+', encoding="utf-8", newline='') as csvfile:
            writer = csv.writer(csvfile)
            if type(text) is str:
                for i in text.split("\n"):
                    writer.writerow([i])
            else:
                for i in text:
                    writer.writerow([i])
        return

    def crawlAndSaveToFiles(self):
        urlsToVisit = self.getUrls()
        emailsToFile = self.getEmails()
        textToFile = self.removeTagsFromHtml()

        for i in urlsToVisit:
            print("\nEntering URL: ", i)
            try:
                localInstance = Crawler(i)
            except:
                continue
            emailsToFile.update(localInstance.getEmails())
            # print(localInstance.removeTags()) # to check site content
            textToFile += "\n" + localInstance.removeTagsFromHtml()

        self.writeToCsv(textToFile, "sitesContent")
        self.writeToCsv(emailsToFile, "emailsFound")
        print("\nEmails across the sites found:", emailsToFile)
        print("--Program ended, 2 csv files were created locally containing emails and crawled sites content.")
        return

    def getInvertedIndex(self, text, URL):
        tokens = nltk.tokenize.word_tokenize(text)
        noPunctuation = [t for t in tokens if t not in string.punctuation] # filtr znakow
        pattern = re.compile(r"\b[^\d\W]+\b")
        noDigits = [t for t in noPunctuation if pattern.match(t)]
        invertedIndexDict = {key:[URL] for key in noDigits}
        return invertedIndexDict

    def createInvertedIndex(self):
        urlsToVisit = self.getUrls()
        Builder = self.initialInvertedIndexDict
        for url in urlsToVisit:
            try:
                localCrawl = Crawler(url)
                print(f"Visiting: {localCrawl.initialURL}")
                for key in localCrawl.initialInvertedIndexDict:
                    if key in Builder:
                        Builder[key].extend(localCrawl.initialInvertedIndexDict[key])
                    else:
                        Builder[key] = localCrawl.initialInvertedIndexDict[key]
                    print(Builder)
            except: continue

if __name__ == "__main__":
    URL = input("Enter the URL (press Enter for default): ") or "https://en.wikipedia.org/wiki/Wykop.pl"
    crawler = Crawler(URL)
    crawler.createInvertedIndex()
