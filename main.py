import os
import re
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(
	loader=jinja2.FileSystemLoader(template_dir),
	extensions=["jinja2.ext.autoescape"],
	autoescape=True
)

class Handler(webapp2.RequestHandler):
	def render(self, template, **kw):
		self.response.write(self.render_str(template, **kw))
	
	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(**params)
	
	def write(self, *a, **kw):
		self.response.write(*a, **kw)


def blog_key(name='default'):
	return db.Key.from_path('blogs', name)


class Post(db.Model, Handler):
	created = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)
	title = db.StringProperty(required=True)
	content = db.TextProperty(required=True)

	def render(self):
		self._render_text = self.content.replace('\n', '<br>')
		return self.render_str("post.html", p = self)


class BlogFront(Handler):
	def get(self):
		# posts = Post.all().order('-created')
		posts = db.GqlQuery("select * from Post order by created desc limit 10")
		self.render('front.html', posts=posts)


class PostPage(Handler):
	def get(self, post_id):
		key = db.Key.from_path('Post', int(post_id), parent=blog_key())
		post = db.get(key)

		if not post:
			self.error(404)
			return

		self.render("permalink.html", post=post)


class NewPost(Handler):
	def get(self):
		self.render("newpost.html")

	def post(self):
		subject = self.request.get('subject')
		content = self.request.get('content')

		if subject and content:
			p = Post(parent = blog_key(), title = subject, content=content)
			p.put()
			self.redirect('/blog/%s' %str(p.key().id()))
		else:
			error = "subject and content, please!"
			self.render("newpost.html", subject=subject, content=content, error=error)


class MainPage(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.write(jinja_env)


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/blog', BlogFront),
    ('/blog/newpost', NewPost),
    ('/blog/([0-9]+)', PostPage),
], debug=True)

