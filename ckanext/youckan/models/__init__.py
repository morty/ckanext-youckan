# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ckanext.youckan.models.alert import DatasetAlert
from ckanext.youckan.models.membership import MembershipRequest, Status as MembershipRequestStatus
from ckanext.youckan.models.resource import CommunityResource
from ckanext.youckan.models.reuse_as import ReuseAsOrganization


def setup():
    CommunityResource.setup()
    DatasetAlert.setup()
    MembershipRequest.setup()
    ReuseAsOrganization.setup()
