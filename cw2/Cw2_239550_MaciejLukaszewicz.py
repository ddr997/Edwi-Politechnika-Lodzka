# Cw.2 EDWI (8.04.22) Maciej Lukaszewicz 239550, SRiPM Informatyka
import string

import requests, re, csv
import nltk
from nltk.corpus import stopwords


class Crawler:

    def __init__(self, initialURL):
        self.initialURL = initialURL
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36', }
            self.requestResponse = requests.get(self.initialURL, timeout=3, headers=headers)
            self.requestResponse.encoding = 'utf-8'
            if self.requestResponse.status_code != 200:
                print("Status code different than 200, skipping page!")
        except:
            raise ValueError("Provided invalid URL address.")
        self.textWithHtmlTags = self.requestResponse.text
        self.extensionsToIgnore = [".js", ".css", ".png", ".jpg", ".pdf", ".jpeg", ".ico"]
        self.initialInvertedIndexDict = self.getInvertedIndex(self.removeTagsFromHtml(), self.initialURL)

    def removeTagsFromHtml(self):
        regex = r'<(script|style).*>(.|\n)*?</(script|style)>|<[^>]*>'
        tagsRemoved = re.sub(regex, "", self.textWithHtmlTags)
        whitespacesRemoved = re.sub(r"\s{2,}", "\n", tagsRemoved)
        noSpaceSplitter = re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ', whitespacesRemoved)
        filteredText = noSpaceSplitter
        return filteredText

    def getUrls(self):
        regexForURL = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urlsFound = set(re.findall(regexForURL, self.textWithHtmlTags))
        urlsFound = {i for i in urlsFound if not any(j in i for j in self.extensionsToIgnore)}  # ignore
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

    def getInvertedIndex(self, text, URL):
        tokens = nltk.tokenize.word_tokenize(text)
        tokens = [i for i in tokens if i not in string.punctuation]
        invertedIndexDict = {i:URL for i in tokens}
        print(invertedIndexDict)
        return 0

    def createInvertedIndex(self):
        urlsToVisit = self.getUrls()
        invertedIndex = self.initialInvertedIndexDict
        for url in urlsToVisit:
            localCrawl = Crawler(url)
            crawledInvIndx = localCrawl.initialInvertedIndexDict
            for key in crawledInvIndx:
                if key in invertedIndex:
                    invertedIndex[key] = invertedIndex[key].extend(crawledInvIndx[key])
                else:
                    invertedIndex[key] = crawledInvIndx[key]






if __name__ == "__main__":
    URL = input("Enter the URL (press Enter for default): ") or "http://robotyka.p.lodz.pl/pl/pracownicy"
    crawler = Crawler(URL)
    crawler.initialInvertedIndexDict
