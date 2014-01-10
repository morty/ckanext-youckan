# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import uuid

from datetime import datetime
from urlparse import urljoin

from sqlalchemy import Column, ForeignKey, types, sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

from ckan import model
from ckan.common import g
from ckan.plugins import toolkit

log = logging.getLogger(__name__)
Base = declarative_base()
DB = model.Session


def make_uuid():
    return unicode(uuid.uuid4())


class AlertType(object):
    ILLEGAL = 'illegal'
    TENDENCIOUS = 'tendencious'
    OTHER = 'other'


class DatasetAlert(Base):
    '''
    Notify a probem on a dataset
    '''
    __tablename__ = 'dataset_alert'
    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)

    user_id = Column(types.UnicodeText, ForeignKey(model.User.id), nullable=False, index=True)
    user = relationship(model.User, primaryjoin=user_id == model.User.id,
        backref=backref('alerts', cascade='all,delete'))

    dataset_id = Column(types.UnicodeText, ForeignKey(model.Package.id), nullable=False, index=True)
    dataset = relationship(model.Package, primaryjoin=dataset_id == model.Package.id,
        backref=backref('alerts', cascade='all,delete'))

    type = Column(types.Unicode(12), nullable=False, index=True, default=AlertType.OTHER)
    comment = Column(types.UnicodeText, nullable=False)

    created = Column(types.DateTime, default=datetime.now)

    closed = Column(types.DateTime)
    closed_by_id = Column(types.UnicodeText, ForeignKey(model.User.id))
    closed_by = relationship(model.User, primaryjoin=closed_by_id == model.User.id)
    close_comment = Column(types.UnicodeText)

    def __init__(self, dataset_or_id, user_or_id, type, comment):
        self.comment = comment
        self.type = type

        if isinstance(dataset_or_id, model.Package):
            self.dataset = dataset_or_id
        else:
            self.dataset_id = dataset_or_id

        if isinstance(user_or_id, model.User):
            self.user = user_or_id
        else:
            self.user_id = user_or_id

    @classmethod
    def setup(cls):
        Base.metadata.create_all(model.meta.engine)

    @classmethod
    def get(cls, id):
        return DB.query(cls).filter(cls.id == id).one()

    @classmethod
    def get_open_for(cls, dataset):
        not_closed = DB.query(cls).filter(cls.closed == None)
        if isinstance(dataset, model.Package):
            not_closed = not_closed.filter(cls.dataset == dataset)
        else:
            not_closed = not_closed.filter(cls.dataset_id == dataset)
        return not_closed.all()

    def send_mail(self, user, subject, template, extra=None):
        from ckan.lib.mailer import mail_user

        if not user.email:
            return

        dataset_url = urljoin(g.site_url, toolkit.url_for(
            controller='package',
            action='read',
            id=self.dataset.name,
        ))
        body = toolkit.render(template, {
            'alert': self,
            'user': user,
            'dataset_url': dataset_url,
            'site_title': g.site_title,
            'site_url': g.site_url,
        })
        mail_user(user, subject, body)

    def notify_admins(self):
        subject = toolkit._('New alert for {0}').format(self.dataset.title)

        organization = model.Group.get(self.dataset.owner_org) if self.dataset.owner_org else None

        admins = DB.query(model.User).filter(model.User.sysadmin == True)
        for admin in admins:
            self.send_mail(admin, subject, 'youckan/mail_new_alert.html')

        admin_ids = (u[0] for u in admins.values('id'))
        if organization:
            org_admins = DB.query(model.User).join(model.GroupRole)
            org_admins = org_admins.filter(model.GroupRole.group_id == organization.id)
            org_admins = org_admins.filter(model.GroupRole.role == model.Role.ADMIN)
            org_admins = org_admins.filter(~model.User.id.in_(admin_ids))
            for admin in org_admins:
                self.send_mail(admin, subject, 'youckan/mail_new_alert.html')
