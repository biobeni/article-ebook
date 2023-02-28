from article_ebook.publisher import Publisher, register_publisher
import requests
from bs4 import BeautifulSoup

class bioRxiv(Publisher):
    """Class for bioRxiv articles"""

    name = "bioRxiv"
    domains = ["biorxiv.org"]

    def get_doi(self):
        if self.doi == None:
            doi_raw = self.soup.find('span', {'class': 'highwire-cite-metadata-doi'}).text.split('/')
            self.doi = str(doi_raw[3]+'/'+doi_raw[4])

    def get_abstract(self):
        """Get article abstract"""
        self.abstract = self.soup.find('div',class_='abstract')

    def get_keywords(self):
        """Get article keywords"""

    def get_body(self):
        """Get body of article"""
        body_raw = self.soup.find('div', class_='fulltext-view')

        for fig in body_raw.find_all('div', class_='fig'):
            try:
                caption = fig.find('div', class_='fig-caption')
                fig.insert_after(caption)
            except:
                pass

            imgsrc = str(fig.find('a', class_='fragment-images')['href'])
            img = self.soup.new_tag('img', src=imgsrc)
            fig.insert_after(img)
            fig.decompose()

        for table in body_raw.find_all('div', class_='table'):
            popup_link = table.find('li', class_='view-popup')
            popup = "https://www.biorxiv.org/" + str(popup_link.find('a')['href'])
            response = requests.get(popup)
            soup = BeautifulSoup(response.text, 'html.parser')

            imgsrc = soup.find('img')['data-src']
            img = soup.new_tag('img', src=imgsrc)
            table.insert_after(img)

            try:
                caption = table.find('div', class_='table-caption')
                table.insert_after(caption)
            except:
                pass

            table.decompose() 

        body_parts = body_raw.find_all('div', class_='section', recursive=False)

        self.body = ''

        for i in body_parts:
            if "abstract" in i["class"] or "ref-list" in i["class"]:
                continue

            self.body += str(i)

    def get_references(self):
        """Get references list"""
        references_raw = self.soup.find('ol', class_='cit-list')
        self.references = '<h2>References</h2>\n'+str(references_raw)

register_publisher(bioRxiv)
