from blog import app
from models import Post
from decorators import login_required

from flask import render_template, flash, url_for, redirect
from flaskext import wtf
from flaskext.wtf import validators

from google.appengine.api import users

class PostForm(wtf.Form):
    title = wtf.TextField('Title', validators=[validators.Required()])
    content = wtf.TextAreaField('Content', validators=[validators.Required()])

@app.route('/posts')
def list_posts():
    posts = Post.all()
    return render_template('list_posts.html', posts=posts)

@app.route('/posts/new', methods = ['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title = form.title.data,
                    content = form.title.content,
                    author = users.get_current_user())
        post.put()
        flash('Post saved on database.')
        return redirect(url_for('list_posts'))
    return render_template('new_post.html', form=form)
