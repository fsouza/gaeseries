# -*- coding: utf-8 -*-
from tipfy import RequestHandler
from tipfy.ext.jinja2 import render_response
from models import Post

class PostListingHandler(RequestHandler):
    def get(self):
        posts = Post.all()
        return render_response('list_posts.html', posts=posts)
