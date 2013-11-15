# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan import model

from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func, desc, null

from ckanext.etalab.model import CertifiedPublicService

DB = model.meta.Session

log = logging.getLogger(__name__)


def datasets_and_organizations():
    '''Query dataset with their organization'''
    query = DB.query(model.Package, model.Group)
    query = query.outerjoin(model.Group, model.Group.id == model.Package.owner_org)
    query = query.outerjoin(CertifiedPublicService)
    query = query.filter(~model.Package.private)
    query = query.filter(model.Package.state == 'active')
    query = query.options(joinedload(model.Group.certified_public_service))
    return query


def organizations_and_counters():
    '''Query organizations with their counters'''
    query = DB.query(model.Group, func.count(model.Package.owner_org).label('nb_datasets'))
    query = query.join(model.GroupRevision)
    query = query.outerjoin(model.Package, model.Group.id == model.Package.owner_org)
    query = query.outerjoin(CertifiedPublicService)
    query = query.group_by(model.Group.id, CertifiedPublicService.organization_id)
    query = query.filter(model.GroupRevision.state == 'active')
    query = query.filter(model.GroupRevision.current == True)
    query = query.filter(model.GroupRevision.is_organization == True)
    query = query.filter(~model.Package.private)
    query = query.filter(model.Package.state == 'active')
    query = query.order_by(
        CertifiedPublicService.organization_id == null(),
        desc('nb_datasets'),
        model.Group.title
    )
    query = query.options(joinedload('certified_public_service'))
    return query
