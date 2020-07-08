source_folder = "publish/"
destination_folder = "html/"
template_folder = "parts/"
aside_folder = "aside/"
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
from distutils import dir_util

def test_is_file(self):
    try:
        assert self.is_file()
    except:
        return

def _copy(self, target):
    test_is_file(self)
    copy(str(self), str(target))  # str() only there for Python < (3, 6)

def _move(self, target):
    test_is_file(self)
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

def get_date_stamps(*times):
    return [timestamps for time in times for timestamps in (time.strftime("%m/%d/%Y %H:%M:%S"), time.strftime("%m/%d/%Y"))]
    
def insert_write_time(post, now = datetime.now()):
    ptime_html, mtime_html = "<p class=\"published-time\">Published on <time datetime=\"{0}\">{1}</time>", " and last modified <time datetime=\"{2}\">{3}</time>" 
    index = post.metadata.published_time_index or (post.metadata.article_title_index or 0) + 1
    if not post.metadata.published_time:
        post.content.insert(index, ptime_html.format(*get_date_stamps(now)))
    elif post.last_modified.date() > post.metadata.published_time.date():
        post.content[index] = (ptime_html + mtime_html).format(*get_date_stamps(post.metadata.published_time, post.last_modified))
    else:
        return post
    post.source.write_text(str(post))
    return Post(post.source)

class ArticleParser(HTMLParser):
    article_title_index =  None
    article_title = None
    published_time_index = None
    published_time = None
    category = None
    open_tag = None

    def parse_published_time(self, tag, attrs):
        if (self.published_time is None
        and tag == 'time'
        and len(attrs) > 0
        and len(attrs[0]) > 1
        and attrs[0][0] == 'datetime'):
            try:
                self.published_time = datetime.strptime(attrs[0][1], "%m/%d/%Y %H:%M:%S")
            except ValueError:
                pass

    def parse_category(self, tag, attrs):
        if (self.category is None
        and tag == "category"
        and len(attrs) > 0
        and len(attrs[0]) > 1
        and attrs[0][0] == "type"):
            self.category = attrs[0][1]

    def handle_starttag(self, tag, attrs):
        self.parse_published_time(tag, attrs)
        self.parse_category(tag, attrs)
        self.open_tag = tag

    def handle_endtag(self, tag):
        self.open_tag = None

    def handle_data(self, data):
        if self.article_title is None and self.open_tag == "h1":
           self.article_title = data

    def is_not_done(self):
        return self.article_title_index is None or self.published_time_index is None or self.category is None
        
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

    def __str__(self):
        return "\n".join("%s: %s" % item for item in vars(self).items())


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

def get_icon_path(post):
    if post.metadata.category:
        return "<img src={0}.svg/>".format(post.metadata.category)
    return ""

def get_html_index_list_item(post):
    return ("<li>{3}<a href=\"{0}\">{1}</a>{2}\n".format(
        post.filename,
        post.metadata.article_title,
        post.metadata.published_time.strftime(" – %b %-d"),
        get_icon_path(post)))

def generate_html_index(posts):
    html_index = ["<ul class=\"posts\">"]
    [html_index.append(get_html_index_list_item(post)) for post in posts]
    html_index.append("</ul>")
    return "\n".join(html_index)


def compile(posts):
    template_path = Path(template_folder)
    destination_path = Path(destination_folder)
    aside_path = Path(aside_folder)
    header = (template_path / page_header).read_text()
    footer = (template_path / page_footer).read_text()
    index_header = (template_path / index_header_file).read_text()
    index_html = header + index_header + generate_html_index(posts) + footer
    [os.remove(file) for file in destination_path.glob("*") if file.is_file()]
    [post.destination.write_text(header + str(post) + footer) for post in posts]
    [(destination_path / file.name).write_text(header + (file.read_text()) + footer) for file in aside_path.glob("*")]
    [file.copy(destination_path / file.name) for file in template_path.glob("*")]
    dir_util.copy_tree((source_folder + "attachments/"),(destination_folder + "attachments/"),preserve_mode=0)
    (destination_path / "index.html").write_text(index_html)

def get_posts():
    posts = [
        Post(file_path)
        for file_path in Path(source_folder).glob("*")
        if file_path.is_file()
    ]
    posts = [insert_write_time(fix_file_name(post)) for post in posts]
    posts.sort(key=lambda x: x.metadata.published_time, reverse=True)
    return posts

compile(get_posts())
