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
_ = lambda s: s

def make_uuid():
    return unicode(uuid.uuid4())


class AlertType(object):
    ILLEGAL = 'illegal'
    TENDENCIOUS = 'tendencious'
    OTHER = 'other'


ALERT_TYPE_NAMES = {
    AlertType.ILLEGAL: 'Contenu illégal',
    AlertType.TENDENCIOUS: 'Contenu tendencieux',
    AlertType.OTHER: 'Autre',
}


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

    def close(self, user, comment=None):
        self.closed = datetime.now()
        self.closed_by = user
        self.close_comment = comment

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
            'names': ALERT_TYPE_NAMES,
            'organization': model.Group.get(self.dataset.owner_org) if self.dataset.owner_org else None,
        })

        mail_user(user, subject, body)

    def notify_admins(self):
        subject = 'Nouvelle alerte pour {0}'.format(self.dataset.title)

        owners = DB.query(model.User).join(model.PackageRole)
        owners = owners.filter(model.PackageRole.package_id == self.dataset.id)
        owners = owners.filter(model.PackageRole.role == model.Role.ADMIN)

        admins = DB.query(model.User).filter(model.User.sysadmin == True)

        queries = [owners, admins]

        organization = model.Group.get(self.dataset.owner_org) if self.dataset.owner_org else None
        if organization:
            org_members = DB.query(model.User)
            org_members = org_members.join(model.Member, model.Member.table_id == model.User.id)
            org_members = org_members.filter(
                model.Member.group == organization,
                model.Member.state == 'active',
                model.Member.table_name == 'user',
            )

            queries.append(org_members)

        queries = (q.subquery().select() for q in queries)
        users = DB.query(model.User).select_from(sql.union(*queries))

        for user in users:
            self.send_mail(user, subject, 'youckan/mail_new_alert.html')
