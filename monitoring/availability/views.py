# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view()
def status(requst):
    if int(time.time()) % 2:
        return Response("Everything OK")
    else:
        return Response("Everything NOT ok.")
