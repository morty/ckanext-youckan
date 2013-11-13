# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan import model
from ckan.model import Related
from ckan.plugins import toolkit

from ckanext.youckan.controllers.base import YouckanBaseController

DBSession = model.meta.Session

log = logging.getLogger(__name__)


class YouckanReuseController(YouckanBaseController):
    def toggle_featured(self, dataset_name, reuse_id):
        '''
        Mark or unmark a reuse as featured
        '''
        user = toolkit.c.userobj
        if not user or not user.sysadmin:
            raise toolkit.NotAuthorized()

        reuse = Related.get(reuse_id)
        reuse.featured = 0 if reuse.featured else 1
        self.commit()
        DBSession.commit()

        return self.to_json(reuse)
