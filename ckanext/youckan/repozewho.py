# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

import hashlib

from ckan.model import User

from repoze.who.interfaces import IIdentifier, IAuthenticator, IChallenger
from webob import Request, Response
from zope.interface import implements

log = logging.getLogger(__name__)


def plugin(**kwargs):
    return YouckanAuthPlugin(**kwargs)


class YouckanAuthPlugin(object):

    implements(IIdentifier, IChallenger, IAuthenticator)

    def __init__(self, secret=None, login_url=None, session_cookie_name='sessionid',
            auth_cookie_name='youckan.auth', next_url_name='next'):

        if not secret or not login_url:
            raise ValueError('secret and login_url parameters are required')

        self.session_cookie_name = session_cookie_name
        self.auth_cookie_name = auth_cookie_name
        self.secret = secret
        self.login_url = login_url
        self.next_url_name = next_url_name

    def challenge(self, environ, status, app_headers=(), forget_headers=()):
        '''Redirect to YouCKAN login page'''
        request = Request(environ)

        next_url = request.url
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
        signature, username = self.extract_cookie(request.cookies[self.auth_cookie_name])

        if not username or not signature:
            return None

        if not signature == self.sign(username, session_id):
            log.debug('Signature ID mismatch')

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
        '''Remember is YouCKAN responsibility'''
        pass

    def forget(self, request, environ):
        '''Forget is YouCKAN responsibility'''
        pass

    def extract_cookie(self, cookie):
        '''Extract information from YouCKAN cookie'''
        parts = cookie.split('::')
        return parts if len(parts) == 2 else (None, None)

    def sign(self, username, session_id):
        '''Signature algorythm encapsulation'''
        return hashlib.sha256(self.secret + session_id + username).hexdigest()
