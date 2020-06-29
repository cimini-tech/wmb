source_folder = "./publish/"
destination_folder = "./html/"
template_folder = "./parts/"
page_header = "header.html"
page_footer = "footer.html"
index_header = "index-header.html"
html_ext = ".html"

import os
import re
from datetime import datetime
from shutil import move, copy
from html.parser import HTMLParser

def list_files(path):
	return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

def read_file(path):
	if os.path.isfile(path):
		with open(path) as f:
			return f.readlines()
	return [] 

def overwrite_file(path,content):
	with open(path,'w') as f:
		f.writelines(content)

def sanitize_filename(filename, article_title):
	if article_title:
		new_article_title=re.sub(r'[^a-zA-Z0-9 ]','',article_title)
		new_article_title=re.sub(r'\s+','-',new_article_title)
		return (new_article_title).lower() + html_ext
	return filename

def fix_file_name(post):
	if post.filename != post.filename_sanitized:
		move(post.source, (source_folder + post.filename_sanitized))
		return Post(post.filename_sanitized)
	return post

def insert_write_time(post,write_time):
	if not post.metadata.published_time:
	    value = "<p class=\"published-time\">Published on <time datetime=\"" + write_time.strftime("%m/%d/%Y %H:%M:%S") + "\">" + write_time.strftime("%m/%d/%Y") + "</time></p>"
	    content = read_file(post.source)
	    content.insert(((post.metadata.article_title_index or 0)+1), value)
	    overwrite_file(post.source,content)
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
	def __init__(self, filename):
		self.filename = filename
		self.source = source_folder + filename
		content = read_file(self.source)
		self.metadata = ArticleParser()
		self.metadata.parse(content)
		self.filename_sanitized = sanitize_filename(filename,self.metadata.article_title)

def get_html_index_list_item(post):
    return ("<li><a href=\""
        + post.filename
        + "\">"
        + post.metadata.article_title
        + "</a>"
        + post.metadata.published_time.strftime(" – %b %-d")
        + "\n")

def generate_html_index(posts):
    html_index = ["<ul>"]
    [html_index.append(get_html_index_list_item(post)) for post in posts]
    html_index.append("</ul>")
    return html_index

def finalize(posts):
	header = read_file(template_folder + "header.html")
	footer = read_file(template_folder + "footer.html")
	index_header = read_file(template_folder + "index_header.html")
	index_html = header + index_header + generate_html_index(posts) + footer
	print(index_html)
	overwrite_file((destination_folder + "index.html"),index_html)
	for post in posts:
		post_content = header + read_file(post.source) + footer
		overwrite_file((destination_folder + post.filename),post_content)
	for file in list_files(template_folder):
		copy(template_folder + file,destination_folder + file)
		 

now = datetime.now()

posts = [Post(file_path) for file_path in list_files(source_folder)]

posts = [insert_write_time(fix_file_name(post), now) for post in posts]

posts.sort(key=lambda x: x.metadata.published_time, reverse=True)
    
finalize(posts)
