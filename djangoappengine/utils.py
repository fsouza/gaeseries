from google.appengine.api import apiproxy_stub_map
import os

have_appserver = bool(apiproxy_stub_map.apiproxy.GetStub('datastore_v3'))

if have_appserver:
    appid = os.environ.get('APPLICATION_ID')
else:
    try:
        from google.appengine.tools import dev_appserver
        from .boot import PROJECT_DIR
        appconfig, unused = dev_appserver.LoadAppConfig(PROJECT_DIR, {})
        appid = appconfig.application
    except ImportError, e:
        raise Exception('Could not get appid. Is your app.yaml file missing? '
                        'Error was: %s' % e)

on_production_server = have_appserver and \
    not os.environ.get('SERVER_SOFTWARE', '').lower().startswith('devel')
