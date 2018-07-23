# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import viewsets
from models import CloudSite
from serializers import CloudSiteSerializer


class CloudSiteViewSet(viewsets.ModelViewSet):
    queryset = CloudSite.objects.all()
    serializer_class = CloudSiteSerializer
    template_name = 'cloudsites.html'

    def list(self, request):
        ret = super(CloudSiteViewSet, self).list(request)
        # Wrap data in dict so it can display in template.
        ret.data = {'sites': ret.data}
        return ret
