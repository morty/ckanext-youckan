# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest2
import json

import httpretty

from base64 import b64decode, b64encode

from zope.interface.verify import verifyClass

from repoze.who.interfaces import IIdentifier, IAuthenticator, IChallenger
from repoze.who.config import WhoConfig
from repoze.who.middleware import PluggableAuthenticationMiddleware

from webtest import TestApp

from ckanext.youckan.repozewho import YouckanAuthPlugin, plugin as make_plugin
from ckanext.youckan.tests.utils import make_environ


WHO_CONFIG = '''
[plugin:youckan]
use = ckanext.youckan.repozewho:plugin
session_cookie_name = youckan.session
auth_cookie_name = youckan.auth
login_url = http://fake/login/
secret = DJANGO_SECRET_KEY
domain = .domain.com

[general]
request_classifier = repoze.who.classifiers:default_request_classifier
challenge_decider = repoze.who.classifiers:default_challenge_decider

[identifiers]
plugins = youckan

[authenticators]
plugins = youckan

[challengers]
plugins = youckan
'''


class YouckanAuthPluginTest(unittest2.TestCase):

    def _wsgi_app(self):
        parser = WhoConfig("")
        parser.parse(WHO_CONFIG)

        def application(environ, start_response):
            start_response("401 Unauthorized", [])
            return [""]

        return PluggableAuthenticationMiddleware(application,
                                 parser.identifiers,
                                 parser.authenticators,
                                 parser.challengers,
                                 parser.mdproviders,
                                 parser.request_classifier,
                                 parser.challenge_decider)

    def _plugin(self):
        return YouckanAuthPlugin('SECRET_KEY', 'http://fake/login',
            session_cookie_name='youckan.session',
            auth_cookie_name='youckan.auth',
            next_url_name='next',
        )

    def test_implements(self):
        verifyClass(IIdentifier, YouckanAuthPlugin)
        verifyClass(IAuthenticator, YouckanAuthPlugin)
        verifyClass(IChallenger, YouckanAuthPlugin)

    def test_make_plugin_all(self):
        plugin = make_plugin(
            secret='SECRET_KEY',
            login_url='http://fake/login',
            session_cookie_name='session_cookie',
            auth_cookie_name='auth_cookie',
            next_url_name='next_url',
        )
        self.assertEquals(plugin.secret, 'SECRET_KEY')
        self.assertEquals(plugin.login_url, 'http://fake/login')
        self.assertEquals(plugin.session_cookie_name, 'session_cookie')
        self.assertEquals(plugin.auth_cookie_name, 'auth_cookie')
        self.assertEquals(plugin.next_url_name, 'next_url')

    def test_make_plugin_missing(self):
        '''Should raise an exception if some required parameter is missing'''
        with self.assertRaises(ValueError):
            make_plugin()

    def test_identify_with_no_credentials(self):
        '''Should not identify if no credentiel present'''
        plugin = self._plugin()
        environ = make_environ()
        identity = plugin.identify(environ)
        self.assertEquals(identity, None)

    def set_session_cookie(self, request, session_id):
        pass

    def set_auth_cookie(self, request, session_id, username, secret):
        pass

    @httpretty.activate
    def test_identify(self):
        '''Should identify if all cookies are presents and valid'''
        plugin = self._plugin()
        token = {
            'access_token': 'token',
            'token_type': 'Bearer',
            'expires_in': '3600',
            'refresh_token': 'refresh-token',
        }
        httpretty.register_uri(httpretty.POST, plugin.token_endpoint, body=json.dumps(token))

        state = b64encode(json.dumps({'came_from': 'initial-page'}))
        environ = make_environ(PATH_INFO=plugin.redirect_url, QUERY_STRING='state={0}&code=code'.format(state))
        identity = plugin.identify(environ)
        self.assertIn('youckan.token', identity)
        self.assertEquals(identity['youckan.token'], token)
        self.assertIn('came_from', identity)
        self.assertEquals(identity['came_from'], 'initial-page')

    @httpretty.activate
    def test_identify_bad_signature(self):
        plugin = self._plugin()
        token = {
            'access_token': 'token',
            'token_type': 'Bearer',
            'expires_in': '3600',
            'refresh_token': 'refresh-token',
        }
        httpretty.register_uri(httpretty.POST, plugin.token_endpoint, body=json.dumps(token))

        state = b64encode(json.dumps({'came_from': 'initial-page'}))
        environ = make_environ(False, PATH_INFO=plugin.redirect_url, QUERY_STRING='state={0}&code=code'.format(state))
        with self.assertRaises(InsecureTransportError):
            plugin.identify(environ)

    def test_challenge(self):
        pass
