# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan import plugins
from ckan.plugins import toolkit


log = logging.getLogger(__name__)

# URLs mapping: format (name, pattern, controller method)
URLS = (
    ('youckan_profile', '/youckan/profile/:username', 'profile'),
    ('youckan_my_datasets', '/youckan/profile/:username/datasets', 'my_datasets'),
    ('youckan_my_organizations', '/youckan/profile/:username/organizations', 'my_organizations'),
    ('youckan_my_valorizations', '/youckan/profile/:username/valorizations', 'my_valorizations'),
    ('youckan_my_usefuls', '/youckan/profile/:username/usefuls', 'my_usefuls'),
)


class YouckanPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)

    def before_map(self, map):
        controller = 'ckanext.youckan.controller:YouckanController'
        for name, pattern, action in URLS:
            map.connect(name, pattern, controller=controller, action=action)
        return map

    def after_map(self, map):
        return map
