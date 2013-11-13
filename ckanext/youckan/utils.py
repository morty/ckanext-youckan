# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import json

from datetime import datetime

from ckan import model

log = logging.getLogger(__name__)


class YouckanJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, model.DomainObject):
            return obj.as_dict()
        return super(YouckanJsonEncoder, self).default(obj)
