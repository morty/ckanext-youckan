# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ckanext.youckan.models.membership import MembershipRequest, Status as MembershipRequestStatus
from ckanext.youckan.models.reuse_as import ReuseAsOrganization
from ckanext.youckan.models.resource import CommunityResource


def setup():
    MembershipRequest.setup()
    ReuseAsOrganization.setup()
    CommunityResource.setup()
