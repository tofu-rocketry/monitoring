# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.db.models import Max

from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer

from models import CloudSite, VAnonCloudRecord
from serializers import CloudSiteSerializer


class CloudSiteViewSet(viewsets.ModelViewSet):
    queryset = CloudSite.objects.all()
    serializer_class = CloudSiteSerializer
    template_name = 'cloudsites.html'

    def list(self, request):
        last_fetched = CloudSite.objects.aggregate(Max('fetched'))['fetched__max']
        print last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20)
        if last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)):
            print 'Out of date'
            fetchset =  VAnonCloudRecord.objects.using('repository').raw("SELECT b.SiteName, COUNT(DISTINCT VMUUID), CloudType, b.UpdateTime FROM (SELECT SiteName, MAX(UpdateTime) AS latest FROM VAnonCloudRecords WHERE UpdateTime>'2018-07-25' GROUP BY SiteName) AS a INNER JOIN VAnonCloudRecords AS b ON b.SiteName = a.SiteName AND b.UpdateTime = a.latest GROUP BY SiteName")
            for f in fetchset:
                CloudSite.objects.update_or_create(defaults={'script': f.CloudType, 'updated': f.UpdateTime}, name=f.SiteName)
        else:
            print 'No need to update'

        response = super(CloudSiteViewSet, self).list(request)
        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {'sites': response.data, 'last_fetched': last_fetched}
        return response
