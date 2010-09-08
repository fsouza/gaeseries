from tipfy import Rule

def get_rules(app):
    rules = [
        Rule('/posts', endpoint='post-listing', handler='apps.blog.handlers.PostListingHandler'),
        Rule('/posts/new', endpoint='new-post', handler='apps.blog.handlers.NewPostHandler'),
    ]

    return rules
