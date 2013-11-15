# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import json

from datetime import datetime

from ckan import model
from ckan.plugins import toolkit

from ckanext.youckan.utils import YouckanJsonEncoder

DBSession = model.meta.Session

log = logging.getLogger(__name__)


class YouckanBaseController(toolkit.BaseController):

    def query(self, *args, **kwargs):
        return DBSession.query(*args, **kwargs)

    def commit(self):
        DBSession.commit()

    def to_json(self, data):
        return json.dumps(data, cls=YouckanJsonEncoder)

    def json_response(self, data):
        toolkit.response.headers[bytes('Content-Type')] = bytes('application/json')
        return self.to_json(data)

    def _build_datasets(self, query):
        '''Build datasets for display from a queryset'''
        return [self._build_dataset(dataset, organization) for dataset, organization in query]

    def _build_dataset(self, dataset, organization):
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

        return {
            'name': dataset.name,
            'title': dataset.title,
            'display_name': dataset.title or dataset.name,
            'notes': dataset.notes,
            'organization': self._build_organization(organization),
            'temporal_coverage': temporal_coverage,
            'territorial_coverage': {
                'name': dataset.extras.get('territorial_coverage', None),
                'granularity': dataset.extras.get('territorial_coverage_granularity', None),
            },
            'periodicity': dataset.extras.get('dct:accrualPeriodicity', None),
        }

    def _build_organizations(self, query):
        return [self._build_organization(organization, nb_datasets) for organization, nb_datasets in query]

    def _build_organization(self, organization, nb_datasets=None):
        return {
            'id': organization.id,
            'name': organization.name,
            'title': organization.title,
            'description': organization.description,
            'image_url': organization.image_url,
            'created': organization.created,
            'approval_status': organization.approval_status,
            'state': organization.state,
            'revision_id': organization.revision_id,
            'certified_public_service': bool(organization.certified_public_service),
            'nb_datasets': nb_datasets,
        }
