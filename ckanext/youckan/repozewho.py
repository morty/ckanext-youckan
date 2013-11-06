# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan.model import User

from ckanext.oauth2.repozewho import OAuth2Plugin

log = logging.getLogger(__name__)


def plugin(**kwargs):
    return OAuth2Plugin(**kwargs)


class YouckanPlugin(OAuth2Plugin):
    def __init__(self, api_endpoint=None, **kwargs):
        super(YouckanPlugin, self).__init__(**kwargs)
        if not api_endpoint:
            raise ValueError('api_endpoint parameter is required')
        self.api_endpoint = api_endpoint

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

    def get_user(self, oauth, **kwargs):
        profile_response = oauth.get(self.profile_api_url)
        user_data = profile_response.json()
        username = user_data[self.profile_api_user_field]
        return User.by_name(username)
