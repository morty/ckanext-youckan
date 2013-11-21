# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan import model

from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.sql import func, desc, null, distinct, and_

from ckanext.etalab.model import CertifiedPublicService

DB = model.meta.Session

log = logging.getLogger(__name__)


def datasets_and_organizations(private=False):
    '''Query dataset with their organization'''
    query = DB.query(model.Package, model.Group)
    query = query.outerjoin(model.Group, model.Group.id == model.Package.owner_org)
    query = query.outerjoin(CertifiedPublicService)
    query = query.filter(model.Package.state == 'active')
    if private:
        query = query.filter(model.Package.private == True)
    else:
        query = query.filter(~model.Package.private)
    query = query.options(joinedload(model.Group.certified_public_service))
    return query


def organizations_and_counters():
    '''Query organizations with their counters'''
    memberships = aliased(model.Member)

    query = DB.query(model.Group,
        func.count(distinct(model.Package.id)).label('nb_datasets'),
        func.count(distinct(memberships.id)).label('nb_members')
    )
    query = query.outerjoin(CertifiedPublicService)
    query = query.outerjoin(model.Package, and_(
        model.Group.id == model.Package.owner_org,
        ~model.Package.private,
        model.Package.state == 'active',
    ))
    query = query.outerjoin(memberships, and_(
        memberships.group_id == model.Group.id,
        memberships.state == 'active',
        memberships.table_name == 'user'
    ))
    query = query.filter(model.Group.state == 'active')
    query = query.filter(model.Group.approval_status == 'approved')
    query = query.filter(model.Group.is_organization == True)
    query = query.group_by(model.Group.id, CertifiedPublicService.organization_id)
    query = query.order_by(
        CertifiedPublicService.organization_id == null(),
        desc('nb_datasets'),
        desc('nb_members'),
        model.Group.title
    )
    return query
