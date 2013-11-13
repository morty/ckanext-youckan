# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan import plugins
from ckan.plugins import toolkit

from ckanext.oauth2.plugins import OAuth2Plugin


log = logging.getLogger(__name__)

# URLs mapping: format (name, pattern, controller method)
URLS = {
    'profile': (
        ('youckan_profile', '/youckan/profile/:username', 'profile'),
        ('youckan_my_datasets', '/youckan/profile/:username/datasets', 'my_datasets'),
        ('youckan_my_organizations', '/youckan/profile/:username/organizations', 'my_organizations'),
        ('youckan_my_valorizations', '/youckan/profile/:username/valorizations', 'my_valorizations'),
        ('youckan_my_usefuls', '/youckan/profile/:username/usefuls', 'my_usefuls'),
    ),
    'dataset': (
        ('youckan_fork', '/youckan/dataset/:dataset_name/fork', 'fork'),
    ),
    'reuse': (
        ('youckan_reuse_featured', '/youckan/dataset/:dataset_name/reuse/:reuse_id/featured', 'toggle_featured'),
    ),
}


class YouckanPlugin(OAuth2Plugin):
    plugins.implements(plugins.IRoutes, inherit=True)

    def before_map(self, map):
        for basename, mapping in URLS.items():
            controller = 'ckanext.youckan.controllers.{0}:Youckan{1}Controller'.format(basename, basename.title())
            for name, pattern, action in mapping:
                map.connect(name, pattern, controller=controller, action=action)
        return map

    def after_map(self, map):
        return map

    # def identify(self):
    #     '''
    #     Open and close sessions following YouCKAN session cookie.

    #     Log user if youckan session is present and vice-versa.
    #     '''
    #     print 'youckan identify'
    #     print 'cookies', toolkit.request.cookies
    #     youckan_session_cookie = toolkit.request.cookies.get('youckan_session')
    #     authtkt_cookie = toolkit.request.cookies.get('auth_tkt')
        # if youckan_session_cookie and not authtkt_cookie:
        #     # Trigger a login (will be redirected)
        #     return toolkit.abort(401, 'Force OAuth2 check')
        # elif authtkt_cookie and not youckan_session_cookie:
        #     # Disconnect user
        #     self.logout()
