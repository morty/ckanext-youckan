# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import json

from datetime import datetime

from ckan import model
from ckan.plugins import toolkit

from ckanext.youckan import queries

DBSession = model.meta.Session

log = logging.getLogger(__name__)


class YouckanJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, model.DomainObject):
            return obj.as_dict()
        return super(YouckanController, self).default(obj)


class YouckanController(toolkit.BaseController):
    def profile(self, username):
        user = model.User.get(username)

        data = {
            'name': username,
            'datasets': self._build_datasets(self._my_datasets_query(user).limit(20)),
            'valorizations': list(self._my_valorizations_query(user).limit(20)),
            'usefuls': self._build_datasets(self._my_usefuls_query(user).limit(20)),
            'organizations': list(self._my_organizations_query(user).limit(20)),
        }
        return json.dumps(data, cls=YouckanJsonEncoder)

    def my_datasets(self, username):
        user = model.User.get(username)
        queryset = self._my_datasets_query(user).limit(20)
        return json.dumps(self._build_datasets(queryset), cls=YouckanJsonEncoder)

    def my_valorizations(self, username):
        user = model.User.get(username)
        queryset = self._my_valorizations_query(user).limit(20)
        return json.dumps(list(queryset), cls=YouckanJsonEncoder)

    def my_organizations(self, username):
        user = model.User.get(username)
        queryset = self._my_organizations_query(user).limit(20)
        return json.dumps(list(queryset), cls=YouckanJsonEncoder)

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

    def _build_datasets(self, query):
        '''Build datasets for display from a queryset'''
        datasets = []

        for dataset, organization in query:

            temporal_coverage = {
                'from': dataset.extras.get('temporal_coverage_from', None),
                'to': dataset.extras.get('temporal_coverage_to', None),
            }
            try:
                temporal_coverage['from'] = datetime.strptime(temporal_coverage['from'], '%Y-%m-%d')
            except:
                pass
            try:
                temporal_coverage['to'] = datetime.strptime(temporal_coverage['to'], '%Y-%m-%d')
            except:
                pass

            datasets.append({
                'name': dataset.name,
                'title': dataset.title,
                'display_name': dataset.title or dataset.name,
                'notes': dataset.notes,
                'organization': organization,
                'temporal_coverage': temporal_coverage,
                'territorial_coverage': {
                    'name': dataset.extras.get('territorial_coverage', None),
                    'granularity': dataset.extras.get('territorial_coverage_granularity', None),
                },
                'periodicity': dataset.extras.get('"dct:accrualPeriodicity"', None),
            })

        return datasets
