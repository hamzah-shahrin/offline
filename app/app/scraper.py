import requests
import html2text
import markdown2
import os
from app import app
from urllib import parse
from ebooklib import epub
from bs4 import BeautifulSoup

t_url_1 = 'https://forums.spacebattles.com/threads/constellations-worm-okami.414320/reader/'
t_url_2 = 'https://forums.sufficientvelocity.com/threads/constellations-worm-okami.31091/reader/'
t_url_3 = 'https://forums.spacebattles.com/threads/a-fox-in-paradise-touhou-thread-two.702973/reader/'
t_url_4 = 'https://forums.spacebattles.com/threads/no-braver-worm-my-hero-academia.880082/'

acceptable_netloc = ['forums.spacebattles.com', 'forums.sufficientvelocity.com']


class ThreadParser:

    def __init__(self, url):
        self.url = self.parse_url(url)
        self.parser = html2text.HTML2Text()
        self.posts = []
        self.labels = []
        self.pages = 0
        self.author = ''
        self.title = ''
        self.counter = 0
        self.parse_thread()

    def get_data(self):
        return [self.title, self.author, self.labels, self.posts]

    @staticmethod
    def parse_url(url):
        url = parse.urlparse(url)
        if url.netloc not in acceptable_netloc:
            print("URL not supported")
        path = '/'.join([''] + list(filter(None, url.path.split('/')))[:2] + ['reader/'])
        return str(url.scheme + '://' + url.netloc + path)

    def parse_thread(self):
        soup = BeautifulSoup(requests.get(self.url).text, 'html.parser')
        try:
            self.pages = int(soup.select('li.pageNav-page > a')[-1].text)
        except IndexError:
            self.pages = 1
        self.author = soup.find('a', class_='username').text
        self.title = soup.find('h1', class_='p-title-value').text.strip()
        for i in range(1, self.pages + 1):
            soup = BeautifulSoup(requests.get(self.url + f'page-{i}').text, 'html.parser')
            self.parse_thread_page(soup)

    def parse_thread_page(self, soup):
        labels = [self.parser.handle(str(i)).strip() for i in soup.find_all('span', class_='threadmarkLabel')]
        self.labels += labels
        posts = soup.find_all('article', class_='message-body js-selectToQuote')
        if len(posts) == 11:
            posts = posts[1:]
        for i, j in enumerate(posts):
            self.posts.append(f'<h1>{labels[i]}</h1>\n\n' + self.parse_thread_post(j))

    def parse_thread_post(self, post):
        self.counter += 1
        return markdown2.markdown(self.parser.handle(str(post)))


class Book:

    def __init__(self, title, author, labels, posts):
        self.title = title
        self.author = author
        self.labels = labels
        self.posts = posts
        self.chapters = []
        self.book = epub.EpubBook()

    def create_book(self):
        self.set_metadata()
        self.add_posts()
        self.set_contents()
        path = os.path.join(app.root_path, 'static\\epub')
        length = len(os.listdir(path))
        epub.write_epub('./app/static/epub/' + str(length + 1)
                        + '.epub', self.book)

    def set_metadata(self):
        self.book.set_identifier(self.title + str(5897234))
        self.book.set_title(self.title)
        self.book.set_language('en')
        self.book.add_author(self.author)

    def set_contents(self):
        self.book.toc = self.chapters
        self.book.spine = ['nav'] + self.chapters
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

    def add_posts(self):
        for index, post in enumerate(self.posts):
            chapter = epub.EpubHtml(title=self.labels[index],
                                    file_name=f'chapter{index}.xhtml',
                                    lang='en', content=post)
            self.chapters.append(chapter)
            self.book.add_item(chapter)


def create_book(link):
    parser = ThreadParser(link)
    book = Book(*parser.get_data())
    book.create_book()
