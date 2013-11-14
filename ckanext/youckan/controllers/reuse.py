# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckan.model import Related
from ckan.plugins import toolkit

from ckanext.youckan.controllers.base import YouckanBaseController

log = logging.getLogger(__name__)


class YouckanReuseController(YouckanBaseController):
    def _toggle_featured(self, reuse_id, featured=None):
        '''
        Mark or unmark a reuse as featured
        '''
        user = toolkit.c.userobj
        if not user or not user.sysadmin:
            raise toolkit.NotAuthorized()

        reuse = Related.get(reuse_id)
        reuse.featured = featured if featured is not None else (0 if reuse.featured else 1)
        self.commit()
        return reuse

        return self.json_response(reuse)

    def toggle_featured(self, reuse_id):
        '''
        Mark or unmark a reuse as featured
        '''
        reuse = self._toggle_featured(reuse_id)
        return self.json_response(reuse)

    def unfeature(self, reuse_id):
        '''
        Unmark a reuse as featured
        '''
        reuse = self._toggle_featured(reuse_id, 0)
        return self.json_response(reuse)

