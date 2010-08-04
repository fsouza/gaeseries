def index():
    posts = db().select(db.posts.ALL)
    return response.render('posts/index.html', locals())

@auth.requires_login()
def new():
    form = SQLFORM(db.posts, fields=['title','content'])
    if form.accepts(request.vars, session):
        response.flash = 'Post saved.'
        redirect(URL('blog', 'posts', 'index'))
    return response.render('posts/new.html', dict(form=form))
