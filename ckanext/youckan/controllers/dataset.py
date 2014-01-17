# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from uuid import uuid1

from ckan import model
from ckan.model import Package
from ckan.plugins import toolkit

from ckanext.youckan.models import DatasetAlert
from ckanext.youckan.controllers.base import YouckanBaseController

DB = model.meta.Session

log = logging.getLogger(__name__)


class YouckanDatasetController(YouckanBaseController):
    def fork(self, dataset_name):
        '''
        Fork this package by duplicating it.

        The new owner will be the user parameter.
        The new package is created and the original will have a new related reference to the fork.
        '''
        if not toolkit.request.method == 'POST':
            raise toolkit.abort(400, 'Expected POST method')

        user = toolkit.c.userobj
        if not user:
            raise toolkit.NotAuthorized('Membership request requires an user')

        dataset = Package.by_name(dataset_name)

        name_width = min(len(dataset.name), 88)
        forked_name = '{name}-fork-{hash}'.format(
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
        extras = [{'key': key, 'value': value} for key, value in dataset.extras.items() if key != 'supplier_id']

        forked = toolkit.get_action('package_create')(data_dict={
            'name': forked_name,
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
        })

        # PackageRole.add_user_to_role(user, model.Role.ADMIN, forked)
        # Manually add the groups to bypass CKAN authorization
        # TODO: Find a better way to handle open groups
        for group in dataset.get_groups():
            group.add_package_by_name(forked_name)
        self.commit()

        # Create the fork relationship
        toolkit.get_action('package_relationship_create')(data_dict={
            'type': 'has_derivation',
            'subject': dataset.id,
            'object': forked['id'],
            'comment': 'Fork',
        })

        return self.json_response(Package.by_name(forked_name))

    def alert(self, dataset_name):
        '''
        Put an alert aka. a signalement on a dataset.
        '''
        if not toolkit.request.method == 'POST':
            raise toolkit.abort(400, 'Expected POST method')

        user = toolkit.c.userobj
        if not user:
            raise toolkit.NotAuthorized('Alert creation requires an user')

        dataset = Package.by_name(dataset_name)

        alert_type = toolkit.request.POST['type']
        comment = toolkit.request.POST['comment']
        alert = DatasetAlert(dataset, user, alert_type, comment)
        DB.add(alert)
        DB.commit()

        alert.notify_admins()

        return self.json_response({
            'id': alert.id,
            'user_id': alert.user_id,
            'dataset_id': alert.dataset_id,
            'type': alert.type,
            'comment': alert.comment,
            'created': alert.created
        })

    def close_alert(self, dataset_name, alert_id):
        '''Delete an alert'''
        if not toolkit.request.method == 'POST':
            raise toolkit.abort(400, 'Expected POST method')

        user = toolkit.c.userobj
        if not user:
            raise toolkit.NotAuthorized('You need to be authenticated to delete an alert')
        elif not user.sysadmin:
            raise toolkit.NotAuthorized('Only sysadmins can delete alert')

        alert = DatasetAlert.get(alert_id)
        alert.close(user, toolkit.request.POST.get('comment'))
        DB.add(alert)
        DB.commit()

        return self.json_response({
            'id': alert.id,
            'user_id': alert.user_id,
            'dataset_id': alert.dataset_id,
            'type': alert.type,
            'comment': alert.comment,
            'created': alert.created,
            'closed': alert.closed,
            'closed_by_id': alert.closed_by_id,
            'close_comment': alert.close_comment,
        })

