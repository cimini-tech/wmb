source_folder = "./publish/"
destination_folder = "./html/"
template_folder = "./parts/"
page_header = "header.html"
page_footer = "footer.html"
index_header = "index-header.html"
html_ext = ".html"

print("Hello World!")

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

def get_element_content(index, content):
	if index >= 0:
		return (re.sub(r'<[^>]+>','',content[index])).strip()

def search(lines, pattern):
	for num, line in enumerate(lines, 1):
		if pattern in line:
			return num
	return 0

def parse_datetime(content, index):
	if index >= 0:
		line = content[index]
		chunks = line.split("\"")
		if len(chunks) >= 4:
			try:
				return datetime.strptime(chunks[3],"%m/%d/%Y %H:%M:%S")
			except ValueError:
				pass

def sanitize_filename(filename, article_title):
	if article_title:
		new_article_title=re.sub(r'[^a-zA-Z0-9 ]','',article_title)
		new_article_title=re.sub(r'\s+','-',new_article_title)
		return (new_article_title).lower() + html_ext
	return filename

def fix_file_name(post):
	if post.filename != post.filename_sanitized:
		move(post.source_path, (source_folder + post.filename_sanitized))
		return Post(post.filename_sanitized)
	return post

def insert_write_time(post,write_time):
	if not post.published_time:
		post.published_time=write_time
		datetime=post.published_time.strftime("%m/%d/%Y %H:%M:%S")
		date=post.published_time.strftime("%m/%d/%Y")
		value = "<p class=\"published-time\">Published on <time datetime=\"" + datetime + "\">" + date + "</time><p>"
		content = read_file(post.source_path)
		content.insert((post.article_title_index+1),value)
		overwrite_file(post.source_path,content)
	return post
		

class Post:
	def __init__(self, filename):
		self.filename = filename
		self.source_path = source_folder + filename
		content = read_file(self.source_path)
		self.article_title_index = search(content, "h1") - 1
		self.article_title = (filename.split("."))[0]
		parsed_article_title = get_element_content(self.article_title_index,content)
		if parsed_article_title:
			self.article_title = parsed_article_title
		self.filename_sanitized=sanitize_filename(filename,self.article_title)
		self.published_time_index = search(content, "p class=\"published-time\"") -1
		self.published_time = parse_datetime(content,self.published_time_index)

def generate_html_index(posts):
	index = []
	index.append("<ul>")
	for post in posts:
		date = post.published_time.strftime(" – %b %-d")
		index.append("<li><a href=\"" + post.filename + "\">" + post.article_title + "</a>" + date + "\n")
	index.append("</ul>")
	return index

def finalize(posts):
	header = read_file(template_folder + "header.html")
	footer = read_file(template_folder + "footer.html")
	index_header = read_file(template_folder + "index_header.html")
	index_html = header + index_header + generate_html_index(posts) + footer
	overwrite_file((destination_folder + "index.html"),index_html)
	for post in posts:
		post_content = header + read_file(post.source_path) + footer
		overwrite_file((destination_folder + post.filename),post_content)
	for file in list_files(template_folder):
		copy(template_folder + file,destination_folder + file)
		 

now = datetime.now()

posts = [insert_write_time(fix_file_name(Post(file_path)), now) for file_path in list_files(source_folder)]
posts.sort(key=lambda x: x.published_time, reverse=True)
finalize(posts)
#print([file_path for file_path in list_files(source_directory)])
