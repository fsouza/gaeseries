def index():
    posts = db().select(db.posts.ALL)
    return response.render('posts/index.html', locals())
