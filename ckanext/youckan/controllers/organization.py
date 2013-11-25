# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging


from ckan import model
from ckan.model import Group
from ckan.plugins import toolkit

from ckanext.youckan.controllers.base import YouckanBaseController
from ckanext.youckan.models import MembershipRequest

DB = model.meta.Session

log = logging.getLogger(__name__)


class YouckanOrganizationController(YouckanBaseController):
    def membership_request(self, org_name):
        '''Request membership for an organization'''
        if not toolkit.request.method == 'POST':
            raise toolkit.abort(400, 'Expected POST method')

        user = toolkit.c.userobj
        if not user:
            raise toolkit.NotAuthorized('Membership request requires an user')

        organization = Group.by_name(org_name)

        comment = toolkit.request.params.get('comment')
        membership_request = MembershipRequest(user, organization, comment)

        DB.add(membership_request)
        DB.commit()

        membership_request.notify_admins()

        return self.json_response({})

    def membership_accept(self, request_id):
        '''Accept a membership request'''
        if not toolkit.request.method == 'POST':
            raise toolkit.abort(400, 'Expected POST method')

        user = toolkit.c.userobj
        if not user:
            raise toolkit.NotAuthorized('Membership validation requires an user')

        membership_request = MembershipRequest.get(request_id)
        membership = membership_request.accept(user)

        return self.json_response(membership)

    def membership_refuse(self, request_id):
        '''Refuse a membership request'''
        if not toolkit.request.method == 'POST':
            raise toolkit.abort(400, 'Expected POST method')

        user = toolkit.c.userobj
        if not user:
            raise toolkit.NotAuthorized('Membership validation requires an user')

        comment = toolkit.request.params.get('comment')

        membership_request = MembershipRequest.get(request_id)
        membership_request.refuse(user, comment)

        return self.json_response({})
