# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import json

from ckan import model

from ckanext.youckan import queries
from ckanext.youckan.utils import YouckanJsonEncoder
from ckanext.youckan.controllers.base import YouckanBaseController

DBSession = model.meta.Session

log = logging.getLogger(__name__)


class YouckanProfileController(YouckanBaseController):
    def profile(self, username):
        user = model.User.get(username)

        data = {
            'name': username,
            'datasets': self._build_datasets(self._my_datasets_query(user).limit(20)),
            'valorizations': list(self._my_valorizations_query(user).limit(20)),
            'usefuls': self._build_datasets(self._my_usefuls_query(user).limit(20)),
            'organizations': list(self._my_organizations_query(user).limit(20)),
        }
        return self.to_json(data)

    def my_datasets(self, username):
        user = model.User.get(username)
        queryset = self._my_datasets_query(user).limit(20)
        return self.to_json(self._build_datasets(queryset))

    def my_valorizations(self, username):
        user = model.User.get(username)
        queryset = self._my_valorizations_query(user).limit(20)
        return self.to_json(list(queryset))

    def my_organizations(self, username):
        user = model.User.get(username)
        queryset = self._my_organizations_query(user).limit(20)
        return self.to_json(list(queryset))

    def my_usefuls(self, username):
        user = model.User.get(username)
        queryset = self._my_usefuls_query(user).limit(20)
        return json.dumps(self._build_datasets(queryset), cls=YouckanJsonEncoder)

    def _my_datasets_query(self, user):
        datasets = queries.datasets_and_organizations()
        datasets = datasets.join(model.PackageRole).filter_by(user=user, role=model.Role.ADMIN)
        return datasets

    def _my_valorizations_query(self, user):
        valorizations = DBSession.query(model.Related).filter(model.Related.owner_id == user.id)
        return valorizations

    def _my_organizations_query(self, user):
        organizations = queries.organizations_and_counters()
        organizations = organizations.join(
            model.Member, model.Member.group_id == model.Group.id
            and
            model.Member.table_name == 'user'
        )
        organizations = organizations.filter(model.Member.state == 'active')
        organizations = organizations.filter(model.Member.table_id == user.id)
        return organizations

    def _my_usefuls_query(self, user):
        usefuls = queries.datasets_and_organizations().join(model.UserFollowingDataset)
        usefuls = usefuls.filter(model.UserFollowingDataset.follower_id == user.id)
        return usefuls
