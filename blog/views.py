from blog import app
from models import Post
from flask import render_template

@app.route('/posts')
def list_posts():
    posts = Post.all()
    return render_template('list_posts.html', posts=posts)
