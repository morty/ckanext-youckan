# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan.model import User

from ckanext.oauth2.repozewho import OAuth2Plugin
from repoze.who.interfaces import IChallengeDecider
from webob import Request
from zope.interface import directlyProvides

from paste.auth import auth_tkt

log = logging.getLogger(__name__)


def plugin(**kwargs):
    return YouckanPlugin(**kwargs)


class YouckanPlugin(OAuth2Plugin):
    def __init__(self, api_endpoint=None, **kwargs):
        if not api_endpoint:
            raise ValueError('api_endpoint parameter is required')
        self.api_endpoint = api_endpoint

        cookie_name = kwargs.pop('cookie_name', 'ckanext.youckan')
        shared_secret = kwargs.pop('shared_secret', None)
        domain = kwargs.pop('domain', None)
        super(YouckanPlugin, self).__init__(cookie_name=cookie_name, **kwargs)

    # def authenticate(self, environ, identity):
    #     '''
    #     Authenticate and extract identity from OAuth2 tokens
    #     '''
    #     request = Request(environ)
    #     log.debug('Repoze authenticate')
    #     log.debug(identity)
    #     if 'oauth2.token' in identity:
    #         oauth = OAuth2Session(self.client_id, token=identity['oauth2.token'])
    #         profile_response = oauth.get(self.profile_api_url)
    #         user_data = profile_response.json()
    #         username = user_data[self.profile_api_user_field]
    #         user = User.by_name(username)
    #         if user is None:
    #             return None
    #         else:
    #             identity.update({'repoze.who.userid': user.name})
    #             self._redirect_from_callback(request, identity)
    #             return user.name
    #     return None

    def get_user(self, oauth, *args, **kwargs):
        log.debug('get user')
        profile_response = oauth.get(''.join([self.api_endpoint, 'me']))
        user_data = profile_response.json()
        username = user_data['slug']
        log.debug('username ' + username)
        return User.by_name(username)

    def identify(self, environ):
        '''Forget identity if Django session is not found'''
        log.debug('youckan repoze identify')
        request = Request(environ)
        if request.path != self.redirect_url and 'youckan_auth' not in request.cookies:
            log.debug('ask forget')
            self.forget(environ, None)
            return None
        return super(YouckanPlugin, self).identify(environ)


def challenge_decider(environ, status, headers):
    log.debug('challenge_decider')
    # print environ, status, headers
    request = Request(environ)
    # if request.path == self.redirect_url:
    #     return False
    print request.cookies
    return status.startswith('401 ')
directlyProvides(challenge_decider, IChallengeDecider)
