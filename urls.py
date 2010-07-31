from django.conf.urls.defaults import *

urlpatterns = patterns('',
    ('^$', 'django.views.generic.simple.direct_to_template',
     {'template': 'home.html'}),
)
