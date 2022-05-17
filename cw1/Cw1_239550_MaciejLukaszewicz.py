import requests, re, csv
# Cw.1 EDWI (8.04.22) Maciej Lukaszewicz 239550, SRiPM Informatyka


class Crawler():

    def __init__(self, initialURL):
        self.initialURL = initialURL
        try:
            headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',}
            self.requestResponse = requests.get(self.initialURL, timeout=3, headers=headers)
            self.requestResponse.encoding = 'utf-8'
            if self.requestResponse.status_code != 200:
                print("Status code different than 200, skipping page!\n")
                raise ValueError
        except:
            raise ValueError("Provided invalid URL address or cannot connect to the page (check internet).")
        self.textWithHtmlTags = self.requestResponse.text
        self.extensionsToIgnore = [".js", ".css", ".png", ".jpg", ".pdf", ".jpeg", ".ico"]

    def removeTags(self):
        regex = r'<(script|style).*>(.|\n)*?</(script|style)>|<[^>]*>'
        tagsRemoved = re.sub(regex, "", self.textWithHtmlTags)
        whitespacesRemoved = re.sub(r"\s{2,}", " ", tagsRemoved)
        filteredText = whitespacesRemoved
        return filteredText

    def getUrls(self):
        regexForURL = r'(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]+\.[a-zA-Z0-9()]+\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*))'
        urlsFound = set(re.findall(regexForURL, self.textWithHtmlTags))
        urlsFound = {i for i in urlsFound if not any(j in i for j in self.extensionsToIgnore)}  # ignore
        print("URLS on the main page: ", urlsFound)
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

        self.writeToCsv(listOfText, "sitesContent")
        self.writeToCsv(listOfEmails, "emailsFound")
        print("\nEmails across the sites found:", initEmails)
        print("--Program ended, 2 csv files were created locally containing emails and crawled sites content.")


if __name__ == "__main__":
    URL = input("Enter the URL (press Enter for default): ") or "http://robotyka.p.lodz.pl/pl/pracownicy"
    crawler = Crawler(URL)
    crawler.crawlAndSaveToFiles()