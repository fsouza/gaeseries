from django.core import urlresolvers, paginator
import urllib

PING_URL = "http://www.google.com/webmasters/tools/ping"

class SitemapNotFound(Exception):
    pass

def ping_google(sitemap_url=None, ping_url=PING_URL):
    """
    Alerts Google that the sitemap for the current site has been updated.
    If sitemap_url is provided, it should be an absolute path to the sitemap
    for this site -- e.g., '/sitemap.xml'. If sitemap_url is not provided, this
    function will attempt to deduce it by using urlresolvers.reverse().
    """
    if sitemap_url is None:
        try:
            # First, try to get the "index" sitemap URL.
            sitemap_url = urlresolvers.reverse('django.contrib.sitemaps.views.index')
        except urlresolvers.NoReverseMatch:
            try:
                # Next, try for the "global" sitemap URL.
                sitemap_url = urlresolvers.reverse('django.contrib.sitemaps.views.sitemap')
            except urlresolvers.NoReverseMatch:
                pass

    if sitemap_url is None:
        raise SitemapNotFound("You didn't provide a sitemap_url, and the sitemap URL couldn't be auto-detected.")

    from django.contrib.sites.models import Site
    current_site = Site.objects.get_current()
    url = "http://%s%s" % (current_site.domain, sitemap_url)
    params = urllib.urlencode({'sitemap':url})
    urllib.urlopen("%s?%s" % (ping_url, params))

class Sitemap(object):
    # This limit is defined by Google. See the index documentation at
    # http://sitemaps.org/protocol.php#index.
    limit = 50000

    def __get(self, name, obj, default=None):
        try:
            attr = getattr(self, name)
        except AttributeError:
            return default
        if callable(attr):
            return attr(obj)
        return attr

    def items(self):
        return []

    def location(self, obj):
        return obj.get_absolute_url()

    def _get_paginator(self):
        if not hasattr(self, "_paginator"):
            self._paginator = paginator.Paginator(self.items(), self.limit)
        return self._paginator
    paginator = property(_get_paginator)

    def get_urls(self, page=1):
        from django.contrib.sites.models import Site
        current_site = Site.objects.get_current()
        urls = []
        for item in self.paginator.page(page).object_list:
            loc = "http://%s%s" % (current_site.domain, self.__get('location', item))
            url_info = {
                'location':   loc,
                'lastmod':    self.__get('lastmod', item, None),
                'changefreq': self.__get('changefreq', item, None),
                'priority':   self.__get('priority', item, None)
            }
            urls.append(url_info)
        return urls

class FlatPageSitemap(Sitemap):
    def items(self):
        from django.contrib.sites.models import Site
        current_site = Site.objects.get_current()
        return current_site.flatpage_set.all()

class GenericSitemap(Sitemap):
    priority = None
    changefreq = None

    def __init__(self, info_dict, priority=None, changefreq=None):
        self.queryset = info_dict['queryset']
        self.date_field = info_dict.get('date_field', None)
        self.priority = priority
        self.changefreq = changefreq

    def items(self):
        # Make sure to return a clone; we don't want premature evaluation.
        return self.queryset.filter()

    def lastmod(self, item):
        if self.date_field is not None:
            return getattr(item, self.date_field)
        return None
