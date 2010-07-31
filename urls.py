from django.conf.urls.defaults import *

urlpatterns = patterns('',
    ('^$', 'django.views.generic.simple.direct_to_template',
     {'template': 'home.html'}),
    ('^login/$', 'django.contrib.auth.views.login'),
    ('^logout/$', 'django.contrib.auth.views.logout'),
    ('^posts/new/$', 'core.views.new_post'),
    ('^posts/$', 'core.views.list_posts'),
)
