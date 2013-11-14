# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan import plugins
from ckan.plugins import toolkit


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
        # ('youckan_reuse_featured', '/youckan/dataset/:dataset_name/reuse/:reuse_id/featured', 'toggle_featured'),
        ('youckan_reuse_featured', '/youckan/reuse/:reuse_id/featured', 'toggle_featured'),
        ('youckan_reuse_unfeature', '/youckan/reuse/:reuse_id/unfeature', 'unfeature'),
    ),
}


def _no_permissions(context, msg):
    user = context['user']
    return {'success': False, 'msg': msg.format(user=user)}


# @toolkit.auth_sysadmins_check
# def user_create(context, data_dict):
#     msg = toolkit._('Users cannot be created.')
#     return _no_permissions(context, msg)


# @toolkit.auth_sysadmins_check
# def user_update(context, data_dict):
#     msg = toolkit._('Users cannot be edited.')
#     return _no_permissions(context, msg)


@toolkit.auth_sysadmins_check
def user_reset(context, data_dict):
    msg = toolkit._('Users cannot reset passwords.')
    return _no_permissions(context, msg)


@toolkit.auth_sysadmins_check
def request_reset(context, data_dict):
    msg = toolkit._('Users cannot reset passwords.')
    return _no_permissions(context, msg)


class YouckanPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthenticator, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.IConfigurable)

    def before_map(self, map):
        for basename, mapping in URLS.items():
            controller = 'ckanext.youckan.controllers.{0}:Youckan{1}Controller'.format(basename, basename.title())
            for name, pattern, action in mapping:
                map.connect(name, pattern, controller=controller, action=action)
        return map

    def configure(self, config):
        '''Store the YouCKAN configuration'''
        self.use_auth = toolkit.asbool(config.get('youckan.use_auth', False))
        if self.use_auth:
            self.logout_url = config['youckan.logout_url']

    def login(self):
        '''Trigger a repose.who challenge'''
        if not self.use_auth:
            pass

        if not toolkit.c.user:
            # A 401 HTTP Status will cause the login to be triggered
            return toolkit.abort(401, toolkit._('Login required!'))

        redirect_to = toolkit.request.params.get('came_from', '/')
        toolkit.redirect_to(bytes(redirect_to))

    def logout(self):
        '''Redirect to YouCKAN logout page'''
        if not self.use_auth:
            pass
        return toolkit.redirect_to(bytes(self.logout_url), locale='default')

    def get_auth_functions(self):
        if not self.use_auth:
            return {}

        # we need to prevent some actions being authorized.
        return {
            # 'user_create': user_create,
            # 'user_update': user_update,
            'user_reset': user_reset,
            'request_reset': request_reset,
        }
