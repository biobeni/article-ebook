from selenium.webdriver import Firefox
from bs4 import BeautifulSoup
import os 
import sys
import pypandoc
from time import sleep
import subprocess
import requests
import json
import tempfile

_publishers = list()
_publisher_domains = dict()
_publisher_names = list()

class Publisher(object):
    """General class for scientific article publishers"""

    def __init__(self, url, doi=None, out_format='epub'):
        self.url = url
        self.doi = doi

    def get_final_url(self):
        pass

    def check_fulltext(self):
        pass

    def soupify(self):
        """Get HTML from article's page"""
        self.get_final_url()
        os.environ['MOZ_HEADLESS'] = '1'
        print('Starting headless browser...',end='',flush=True)
        
        driver = Firefox()
        print('Loading page................',end="",flush=True)
        try:
            driver.get(self.url)
        except:
            sys.exit('Failed to load URL')
        
        if self.doi != None:
            sleep(5) #To allow redirects

        sleep(5)
        print('done')   
        self.url = driver.current_url
        
        self.soup = BeautifulSoup(driver.page_source,'html.parser')
        driver.quit()

    def doi2json(self):
        """Get a dictionary of metadata for a given DOI."""
        url = "http://dx.doi.org/" + self.doi
        headers = {"accept": "application/json"}
        r = requests.get(url, headers = headers)
        self.meta = r.json()

    def get_metadata(self):
        """Extract metadata from DOI"""
        self.doi2json()

        self.title = self.meta['title']

        self.author_surnames = []
        self.author_givennames = []
        for i in self.meta['author']:
            self.author_surnames.append(i['family'])
            self.author_givennames.append(i['given'])

        if 'institution' in self.meta.keys():
            self.journal = self.meta['institution'][0]['name']
        else:
            self.journal = self.meta['container-title']

        if 'published-print' in self.meta.keys():
            self.year = str(self.meta['published-print']['date-parts'][0][0])
        elif 'published-online' in self.meta.keys():
            self.year = str(self.meta['published-online']['date-parts'][0][0])
        else:
            self.year = str(self.meta['published']['date-parts'][0][0])

        try:
            self.volume = str(self.meta['volume'])
        except:
            self.volume = ''
        try:
            self.pages = str(self.meta['page'])
        except:
            self.pages = ''

    def get_citation(self,link=False):
        """Generate a formatted citation from metadata"""
        all_authors = ''
        for i in range(0,len(self.author_surnames)):
            all_authors += self.author_surnames[i] + ', '
            all_authors += self.author_givennames[i]
            if(i != (len(self.author_surnames) - 1)):
                all_authors += '; '
        if all_authors[-1] == '.':
            cap = ' '
        else:
            cap = '. '
        
        if link:
            doi = '<a href="https://dx.doi.org/'+self.doi+'">'+self.doi+'</a>'
        else:
            doi = self.doi

        if self.volume != '':
            return(all_authors+cap+self.year+'. '+self.title+'. ' \
                    +self.journal+' '+self.volume+': '+self.pages+'.' \
                    +' doi: '+doi) 
        else:
            return(all_authors+cap+self.year+'. '+self.title+'. ' \
                    +self.journal+'. '+' doi: '+doi)
    
    def extract_data(self):
        self.check_fulltext()
        print('Extracting data from HTML...',end='',flush=True)
        self.get_doi()
        self.get_metadata()
        self.get_abstract()
        self.get_keywords()
        self.get_body()
        self.get_references()
        print('done')

    def epubify(self,output=None,fileformat=None):
        """Convert data into epub format"""

        all_authors = ''
        for i in range(0,len(self.author_surnames)):
            all_authors += self.author_givennames[i] + ' '
            all_authors += self.author_surnames[i]
            if(i != (len(self.author_surnames) - 1)):
                all_authors += ', '
       
        self.get_citation()

        args = []
        args.append('-M')
        args.append('title='+self.title)
        args.append('-M')
        args.append('author='+all_authors)
        args.append('--webtex')

        if fileformat == None:
            fileformat = 'epub'
        
        if output == None:
            self.output = self.author_surnames[0]+'_'+self.year+'.'+fileformat
        else:
            if output.endswith(fileformat):
                self.output = output
            else:
                self.output = output+'.'+fileformat
        
        output_raw = os.path.join(tempfile.gettempdir(), 'raw.epub')

        combined = ''
        combined += str(self.get_citation(link=True))
        combined += str(self.abstract)
        combined += str(self.body)
        combined += str(self.references)
        
        print('Generating ebook.............',end='',flush=True)
        epubout = pypandoc.convert_text(combined,format='html',to='epub+raw_html',
                extra_args=args,
                outputfile=output_raw)

        cmdline = ['ebook-convert',output_raw,self.output]

        if self.output.endswith('.epub'):
            cmdline.append('--no-default-epub-cover')

        subprocess.check_output(cmdline)
        print('done')

def register_publisher(publisher):
    _publishers.append(publisher)
    _publisher_names.append(publisher.name)
    for d in publisher.domains:
        _publisher_domains[d] = publisher

def get_publishers():
    return _publisher_domains

def list_publishers():
    return _publisher_names

def match_publisher(url,doi):
    """Match a URL to a publisher class"""
    domain = ".".join(url.split("//")[-1].split("/")[0] \
            .split('?')[0].split('.')[-2:])
    if domain == 'doi.org':
        sys.exit('DOI not found; is it correct?')

    try:
        art = get_publishers()[domain](url=url,doi=doi)
        print('Matched URL to publisher: '+art.name)
        return(art)
    except:
        sys.exit('Publisher ['+domain+'] not supported.')

