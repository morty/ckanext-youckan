# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

from ckan import model
from ckan.common import g

log = logging.getLogger(__name__)
Base = declarative_base()
DB = model.Session


class ReuseAsOrganization(Base):
    '''
    Publish a reuse as an Organization
    '''
    __tablename__ = 'reuse_as_org'

    reuse_id = Column(types.UnicodeText, ForeignKey(model.Related.id), nullable=False, primary_key=True)
    reuse = relationship(model.Related, primaryjoin=reuse_id == model.Related.id,
        backref=backref('published_as', cascade='all,delete'))

    organization_id = Column(types.UnicodeText, ForeignKey(model.Group.id), nullable=False, index=True)
    organization = relationship(model.Group, primaryjoin=organization_id == model.Group.id,
        backref=backref('reuse_published_as', cascade='all,delete'))

    def __init__(self, reuse, organization):
        self.reuse = reuse
        self.organization = organization

    @classmethod
    def setup(cls):
        Base.metadata.create_all(model.meta.engine)

    @classmethod
    def get(cls, reuse):
        query = DB.query(cls)
        if isinstance(reuse, model.Related):
            query = query.filter(cls.reuse == reuse)
        else:
            query = query.filter(cls.reuse_id == reuse)
        return query.first()

    @classmethod
    def get_org(cls, reuse):
        published_as = cls.get(reuse)
        return published_as.organization if published_as else None
