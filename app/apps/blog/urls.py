from tipfy import Rule

def get_rules(app):
    rules = [
        Rule('/posts', endpoint='post-listing', handler='apps.blog.handlers.PostListingHandler'),
    ]

    return rules
