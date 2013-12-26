# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan import plugins
from ckan.plugins import toolkit

from ckanext.youckan.models import setup as model_setup


log = logging.getLogger(__name__)

# URLs mapping: format (name, pattern, controller method)
URLS = {
    'profile': (
        ('youckan_profile', '/youckan/profile/:username', 'profile'),
        ('youckan_my_datasets', '/youckan/profile/:username/datasets', 'my_datasets'),
        ('youckan_my_privates', '/youckan/profile/:username/privates', 'my_privates'),
        ('youckan_my_organizations', '/youckan/profile/:username/organizations', 'my_organizations'),
        ('youckan_my_reuses', '/youckan/profile/:username/reuses', 'my_reuses'),
        ('youckan_my_usefuls', '/youckan/profile/:username/usefuls', 'my_usefuls'),
    ),
    'dataset': (
        ('youckan:dataset-fork', '/youckan/dataset/:dataset_name/fork', 'fork'),
        ('youckan:dataset-alert', '/youckan/dataset/:dataset_name/alert', 'alert'),
    ),
    'organization': (
        ('youckan:membership-request', '/youckan/organization/:org_name/membership', 'membership_request'),
        ('youckan:membership-accept', '/youckan/membership/:request_id/accept', 'membership_accept'),
        ('youckan:membership-refuse', '/youckan/membership/:request_id/refuse', 'membership_refuse'),
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


@toolkit.auth_sysadmins_check
def user_create(context, data_dict):
    print 'User create'
    return {'success': True}
    # import ipdb; ipdb.set_trace()
    # msg = toolkit._('Users cannot be created.')
    # return _no_permissions(context, msg)


@toolkit.auth_sysadmins_check
def user_update(context, data_dict):
    print 'User update', context, data_dict
    return {'success': True}


@toolkit.auth_sysadmins_check
def user_reset(context, data_dict):
    msg = toolkit._('Users cannot reset passwords.')
    return _no_permissions(context, msg)


@toolkit.auth_sysadmins_check
def request_reset(context, data_dict):
    msg = toolkit._('Users cannot reset passwords.')
    return _no_permissions(context, msg)


class SentryPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IMiddleware)

    def make_middleware(self, app, config):
        from raven.contrib.pylons import Sentry
        return Sentry(app, config)


class YouckanPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthenticator, inherit=True)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)

    def before_map(self, map):
        for basename, mapping in URLS.items():
            controller = 'ckanext.youckan.controllers.{0}:Youckan{1}Controller'.format(basename, basename.title())
            for name, pattern, action in mapping:
                map.connect(name, pattern, controller=controller, action=action)
        return map

    def configure(self, config):
        '''Store the YouCKAN configuration'''
        if not toolkit.check_ckan_version('2.1'):
            log.warn('This extension has only been tested on CKAN 2.1!')

        self.use_auth = toolkit.asbool(config.get('youckan.use_auth', False))
        if self.use_auth:
            self.logout_url = config['youckan.logout_url']

        model_setup()

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

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
            'user_create': user_create,
            'user_update': user_update,
            'user_reset': user_reset,
            'request_reset': request_reset,
        }
