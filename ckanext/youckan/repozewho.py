# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import hmac
import logging

from base64 import b64encode


from urllib import quote

from ckan.model import User

from itsdangerous import URLSafeTimedSerializer, BadSignature

from repoze.who.interfaces import IIdentifier, IAuthenticator, IChallenger
from webob import Request, Response
from zope.interface import implements

log = logging.getLogger(__name__)


def plugin(**kwargs):
    return YouckanAuthPlugin(**kwargs)


class YouckanAuthPlugin(object):

    implements(IIdentifier, IChallenger, IAuthenticator)

    def __init__(self, secret=None, login_url=None, session_cookie_name='sessionid',
            auth_cookie_name='youckan.auth', next_url_name='next', https=False):

        if not secret or not login_url:
            raise ValueError('secret and login_url parameters are required')

        self.session_cookie_name = session_cookie_name
        self.auth_cookie_name = auth_cookie_name
        self.secret = secret
        self.login_url = login_url
        self.next_url_name = next_url_name
        self.use_https = https
        self.signer = URLSafeTimedSerializer(secret, signer_kwargs={'sep': ':'})

    def challenge(self, environ, status, app_headers=(), forget_headers=()):
        '''Redirect to YouCKAN login page'''
        request = Request(environ)

        next_url = quote(request.url)
        if self.use_https and next_url.startswith('http://'):
            next_url = next_url.replace('http://, https://')
        auth_url = '{0}?{1}={2}'.format(self.login_url, self.next_url_name, next_url)

        response = Response()
        response.status = 302
        response.location = auth_url

        return response

    def identify(self, environ):
        '''Identity user from its Django session and YouCKAN auth cookies'''
        request = Request(environ)

        if not self.session_cookie_name in request.cookies or not self.auth_cookie_name in request.cookies:
            return None

        session_id = request.cookies[self.session_cookie_name]
        cookie = request.cookies[self.auth_cookie_name]

        try:
            username = self.signer.loads(cookie, salt=session_id)
            log.debug('Signature ID mismatch: %s', username)
        except BadSignature:
            return None

        return {'username': username}

    def authenticate(self, environ, identity):
        '''Fetch the user given its username in identity'''
        if 'username' in identity:
            user = User.by_name(identity['username'])
            if user is None:
                return None
            else:
                identity.update({'repoze.who.userid': user.name})
                return user.name
        return None

    def remember(self, environ, identity):
        '''Remember is YouCKAN SSO responsibility'''
        pass

    def forget(self, request, environ):
        '''Forget is YouCKAN SSO responsibility'''
        pass
