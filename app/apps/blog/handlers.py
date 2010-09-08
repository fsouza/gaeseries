# -*- coding: utf-8 -*-
from tipfy import RequestHandler
from tipfy.ext.jinja2 import render_response
from tipfy.ext.auth import login_required, AppEngineAuthMixin
from tipfy.ext.session import AllSessionMixins, SessionMiddleware
from tipfy.ext.wtforms import Form, fields, validators
from models import Post

class PostListingHandler(RequestHandler):
    def get(self):
        posts = Post.all()
        return render_response('list_posts.html', posts=posts)

class PostForm(Form):
    csrf_protection = True
    title = fields.TextField('Title', validators=[validators.Required])
    content = fields.TextAreaField('Content', validators=[validators.Required])

class NewPostHandler(RequestHandler, AppEngineAuthMixin, AllSessionMixins):
    middleware = [SessionMiddleware]

    @login_required
    def get(self):
        form = PostForm(self.request)
        return render_response('new_post.html', form=form)
