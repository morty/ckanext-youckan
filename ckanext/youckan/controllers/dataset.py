# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from uuid import uuid1

from ckan import model
from ckan.model import Package, PackageRole
from ckan.plugins import toolkit

from ckanext.youckan.controllers.base import YouckanBaseController

DBSession = model.meta.Session

log = logging.getLogger(__name__)


class YouckanDatasetController(YouckanBaseController):
    def fork(self, dataset_name):
        '''
        Fork this package by duplicating it.

        The new owner will be the user parameter.
        The new package is created and the original will have a new related reference to the fork.
        '''
        import ipdb; ipdb.set_trace()
        user = toolkit.c.user

        if not user:
            raise ValueError('Fark requires an user')

        dataset = self.query(Package).filter(Package.name == dataset_name).one()

        name_width = min(len(dataset.name), 88)
        name = '{name}-fork-{hash}'.format(
            name=dataset.name[:name_width],
            hash=str(uuid1())[:6],
        )

        orgs = user.get_groups('organization')
        resources = [{
                'url': r.url,
                'description': r.description,
                'format': r.format,
                'name': r.name,
                'resource_type': r.resource_type,
                'mimetype': r.mimetype,
            }
            for r in dataset.resources
        ]
        groups = [{'id': g.id} for g in dataset.get_groups()]
        tags = [{'name': t.name, 'vocabulary_id': t.vocabulary_id} for t in dataset.get_tags()]
        extras = [{'key': key, 'value': value} for key, value in dataset.extras.items()]

        # url = '{0}/api/3/action/package_create'.format(conf['ckan_url'])
        # headers = {
        #     'content-type': 'application/json',
        #     'Authorization': user.apikey,
        # }
        data = {
            'name': name,
            'title': dataset.title,
            'maintainer': user.fullname,
            'maintainer_email': user.email,
            'license_id': dataset.license_id,
            'notes': dataset.notes,
            'url': dataset.url,
            'version': dataset.version,
            'type': dataset.type,
            'owner_org': orgs[0].id if len(orgs) else None,
            'resources': resources,
            'groups': groups,
            'tags': tags,
            'extras': extras,
        }

        forked = toolkit.get_action('package_create')(toolkit.c, data)

        # try:
        #     response = requests.post(url, data=json.dumps(data), headers=headers, timeout=POST_TIMEOUT)
        #     response.raise_for_status()
        # except requests.RequestException:
        #     log.exception('Unable to create dataset')
        #     raise
        # json_response = response.json()

        # if not json_response['success']:
        #     raise Exception('Unable to create package: {0}'.format(json_response['error']['message']))

        # Add the user as administrator
        # forked = model.Session.query(model.Package).get(json_response['result']['id'])
        PackageRole.add_user_to_role(user, model.Role.ADMIN, forked)
        self.commit()

        # Create the fork relationship
        data = {
            'type': 'has_derivation',
            'subject': dataset.id,
            'object': forked.id,
            'comment': 'Fork',
        }
        action = toolkit.get_action('package_relationship_create')
        result = action(toolkit.c, data)

        # url = url = '{0}/api/3/action/package_relationship_create'.format(conf['ckan_url'])
        # try:
        #     response = requests.post(url, data=json.dumps(data), headers=headers, timeout=POST_TIMEOUT)
        #     response.raise_for_status()
        # except requests.RequestException:
        #     log.exception('Unable to create relationship')
        #     return forked

        # json_response = response.json()
        # if not json_response['success']:
        #     log.error('Unable to create relationship: {0}'.format(json_response['error']['message']))

        return self.to_json(data)

