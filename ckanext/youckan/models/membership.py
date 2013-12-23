# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import uuid

from datetime import datetime
from urlparse import urljoin

from sqlalchemy import Column, ForeignKey, types
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


class Status(object):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REFUSED = 'refused'


class MembershipRequest(Base):
    '''
    Pending organization membership requests
    '''
    __tablename__ = 'membership_request'
    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)

    user_id = Column(types.UnicodeText, ForeignKey(model.User.id), nullable=False, index=True)
    user = relationship(model.User, primaryjoin=user_id == model.User.id,
        backref=backref('membership_requests', cascade='all,delete'))

    organization_id = Column(types.UnicodeText, ForeignKey(model.Group.id), nullable=False, index=True)
    organization = relationship(model.Group, primaryjoin=organization_id == model.Group.id,
        backref=backref('membership_requests', cascade='all,delete'))

    status = Column(types.Unicode(8), nullable=False, index=True, default=Status.PENDING)

    created = Column(types.DateTime, default=datetime.now)
    handled_on = Column(types.DateTime)

    handled_by_id = Column(types.UnicodeText, ForeignKey(model.User.id))
    handled_by = relationship(model.User, primaryjoin=handled_by_id == model.User.id)

    comment = Column(types.UnicodeText)
    refusal_comment = Column(types.UnicodeText)

    def __init__(self, user, organization, comment=None):
        self.user = user
        self.organization = organization
        self.comment = comment

    @classmethod
    def setup(cls):
        Base.metadata.create_all(model.meta.engine)

    @classmethod
    def get(cls, id):
        return DB.query(cls).filter(cls.id == id).one()

    @classmethod
    def pending_for(cls, organization):
        pendings = DB.query(cls).filter(cls.status == Status.PENDING)
        if isinstance(organization, model.Group):
            pendings = pendings.filter(cls.organization == organization)
        else:
            pendings = pendings.filter(cls.organization_id == organization)
        return pendings.all()

    @classmethod
    def is_pending(cls, organization, user):
        pendings = DB.query(cls).filter(cls.status == Status.PENDING)
        pendings = pendings.filter(cls.user == user)
        pendings = pendings.filter(cls.organization == organization)
        return pendings.count() > 0

    def send_mail(self, user, subject, template, extra=None):
        from ckan.lib.mailer import mail_user

        org_url = urljoin(g.site_url, toolkit.url_for(
            controller='organization',
            action='read',
            id=self.organization.name,
        ))
        body = toolkit.render(template, {
            'membership': self,
            'user': user,
            'org_url': org_url,
            'site_title': g.site_title,
            'site_url': g.site_url,
        })
        mail_user(user, subject, body)

    def notify_admins(self):
        subject = 'New membership request for {0}'.format(self.organization.display_name)

        admins = DB.query(model.User).join(model.GroupRole)
        admins = admins.filter(model.GroupRole.group_id == self.organization_id)
        admins = admins.filter(model.GroupRole.role == model.Role.ADMIN)

        for admin in admins:
            self.send_mail(admin, subject, 'youckan/mail_membership_request.html')

    def handle(self, user, status):
        self.status = status
        self.handled_by = user
        self.handled_on = datetime.now()
        DB.add(self)
        DB.commit()

    def accept(self, user):
        self.handle(user, Status.ACCEPTED)
        create_action = toolkit.get_action('organization_member_create')
        membership = create_action(data_dict={
            'id': self.organization_id,
            'username': self.user.name,
            'role': model.Role.EDITOR,
        })
        self.send_mail(self.user, 'Membership accepted', 'youckan/mail_membership_accepted.html')
        return membership

    def refuse(self, user, comment):
        self.refusal_comment = comment
        self.handle(user, Status.REFUSED)
        self.send_mail(self.user, 'Membership refused', 'youckan/mail_membership_refused.html')
