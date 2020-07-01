source_folder = "publish/"
destination_folder = "html/"
template_folder = "parts/"
page_header = "header.html"
page_footer = "footer.html"
index_header_file = "index_header.html"
html_ext = ".html"

import os
import re
from datetime import datetime
from shutil import move, copy
from html.parser import HTMLParser
from pathlib import Path

def _copy(self, target):
    assert self.is_file()
    copy(str(self), str(target))  # str() only there for Python < (3, 6)

def _move(self, target):
    assert self.is_file()
    move(str(self), str(target))

Path.copy = _copy
Path.move = _move

def sanitize_filename(filename, article_title):
	if article_title:
		new_article_title=re.sub(r'[^a-zA-Z0-9 ]','',article_title)
		new_article_title=re.sub(r'\s+','-',new_article_title)
		return (new_article_title).lower() + html_ext
	return filename

def fix_file_name(post):
	if post.filename != post.filename_sanitized:
		post.source.move(post.source.parents[0] / post.filename_sanitized)
		return Post(post.source.parents[0] / post.filename_sanitized)
	return post

def insert_write_time(post,write_time):
    if not post.metadata.published_time:
        value = "<p class=\"published-time\">Published on <time datetime=\"{0}\">{1}</time>".format(
                write_time.strftime("%m/%d/%Y %H:%M:%S"),
                write_time.strftime("%m/%d/%Y"))
        post.content.insert(((post.metadata.article_title_index or 0)+1), value)
        post.source.write_text(str(post))
        return Post(post.source)
    elif post.last_modified.date() > post.metadata.published_time.date():
        value = "<p class=\"published-time\">Published on <time datetime=\"{0}\">{1}</time>".format(
                        post.metadata.published_time.strftime("%m/%d/%Y %H:%M:%S"),
                        post.metadata.published_time.strftime("%m/%d/%Y"))
        value = value + " and last modified <time datetime=\"{0}\">{1}</time>".format(
            post.last_modified.strftime("%m/%d/%Y %H:%M:%S"),
            post.last_modified.strftime("%m/%d/%Y"))
        post.content[post.metadata.published_time_index] = value
        post.source.write_text(str(post))
        return Post(post.source)
    return post
		

class ArticleParser(HTMLParser):
    article_title_index =  None
    article_title = None
    published_time_index = None
    published_time = None
    open_tags = []
    
    def handle_starttag(self, tag, attrs):
        if (self.published_time is None
        and tag == 'time'
        and len(attrs) > 0
        and len(attrs[0]) > 1
        and attrs[0][0] == 'datetime'):
            try:
                self.published_time = datetime.strptime(attrs[0][1], "%m/%d/%Y %H:%M:%S")
            except ValueError:
                pass
        self.open_tags.append(tag)

    def handle_endtag(self, tag):
        del self.open_tags[-1]

    def handle_data(self, data):
        if self.article_title is None and self.open_tags[-1] == "h1":
           self.article_title = data

    def is_not_done(self):
        return self.article_title_index is None or self.published_time_index is None
        
    def parse(self, article):
        i = 0
        #article = article.splitlines()
        while self.is_not_done() and i < len(article):
            self.feed(article[i])
            if self.article_title_index is None and self.article_title:
                self.article_title_index = i
            if self.published_time_index is None and self.published_time:
                self.published_time_index = i
            i = i + 1


class Post:
	def __init__(self, filepath):
		self.filename = filepath.name
		self.source = filepath
		self.destination = Path() / destination_folder / self.filename
		self.content = self.source.read_text().splitlines()
		self.metadata = ArticleParser()
		self.metadata.parse(self.content)
		self.filename_sanitized = sanitize_filename(self.filename,self.metadata.article_title)
		self.last_modified = datetime.fromtimestamp(self.source.stat().st_mtime)
	
	def __str__(self): 
	    return "\n".join(self.content)

def get_html_index_list_item(post):
    return ("<li><a href=\"{0}\">{1}</a>{2}\n".format(
        post.filename,
        post.metadata.article_title,
        post.metadata.published_time.strftime(" - %b %-d")))

def generate_html_index(posts):
    html_index = ["<ul>"]
    [html_index.append(get_html_index_list_item(post)) for post in posts]
    html_index.append("</ul>")
    return "\n".join(html_index)


def finalize(posts):
    template_path = Path(template_folder)
    destination_path = Path(destination_folder)
    header = (template_path / page_header).read_text()
    footer = (template_path / page_footer).read_text()
    index_header = (template_path / index_header_file).read_text()
    index_html = header + index_header + generate_html_index(posts) + footer
    [os.remove(file) for file in destination_path.glob("*")]
    [post.destination.write_text(header + str(post) + footer) for post in posts]
    [file.copy(destination_path / file.name) for file in template_path.glob("*")]
    (destination_path / "index.html").write_text(index_html)

now = datetime.now()

posts = [Post(file_path) for file_path in Path(source_folder).glob("*")]

posts = [insert_write_time(fix_file_name(post), now) for post in posts]

posts.sort(key=lambda x: x.metadata.published_time, reverse=True)
    
finalize(posts)
