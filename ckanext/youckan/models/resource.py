# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import uuid

from datetime import datetime

from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

from ckan import model

log = logging.getLogger(__name__)
Base = declarative_base()
DB = model.Session


def make_uuid():
    return unicode(uuid.uuid4())


class CommunityResource(Base):
    '''
    Publish a reuse as an Organization
    '''
    __tablename__ = 'community_resource'
    __mapper_args__ = {'concrete': True}

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)

    owner_id = Column(types.UnicodeText, ForeignKey(model.User.id), nullable=False, index=True)
    owner = relationship(model.User, primaryjoin=owner_id == model.User.id,
        backref=backref('community_resources', cascade='all,delete'))

    dataset_id = Column(types.UnicodeText, ForeignKey(model.Package.id), nullable=False, index=True)
    dataset = relationship(model.Package, primaryjoin=dataset_id == model.Package.id,
        backref=backref('community_resources', cascade='all,delete'))

    name = Column(types.UnicodeText)
    url = Column(types.UnicodeText, nullable=False)
    format = Column(types.UnicodeText)
    description = Column(types.UnicodeText)

    publish_as_id = Column(types.UnicodeText, ForeignKey(model.Group.id), nullable=False, index=True)
    publish_as = relationship(model.Group, primaryjoin=publish_as_id == model.Group.id)

    created = Column(types.DateTime, default=datetime.now)
    last_modified = Column(types.DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, dataset_or_id, owner_or_id):
        if isinstance(dataset_or_id, model.Package):
            self.dataset = dataset_or_id
        else:
            self.dataset_id = dataset_or_id

        if isinstance(owner_or_id, model.User):
            self.owner = owner_or_id
        else:
            self.owner_id = owner_or_id

    @classmethod
    def setup(cls):
        Base.metadata.create_all(model.meta.engine)

    @classmethod
    def get(cls, user_dataset_or_id):
        query = DB.query(cls)
        if isinstance(user_dataset_or_id, model.User):
            return query.filter(cls.owner == user_dataset_or_id)
        elif isinstance(user_dataset_or_id, model.Package):
            return query.filter(cls.dataset == user_dataset_or_id)
        else:
            return query.filter(cls.id == user_dataset_or_id).one()
