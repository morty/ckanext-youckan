# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ckanext.youckan.models.membership import MembershipRequest, Status as MembershipRequestStatus


def setup():
    MembershipRequest.setup()
