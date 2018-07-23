# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework.decorators import api_view
from rest_framework.response import Response

from rest_framework import viewsets
from models import CloudSite
from serializers import CloudSiteSerializer


class CloudSiteViewSet(viewsets.ModelViewSet):
    queryset = CloudSite.objects.all()
    serializer_class = CloudSiteSerializer
