# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.db.models import Max

from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer

from models import GridSite, VSuperSummaries, CloudSite, VAnonCloudRecord
from serializers import GridSiteSerializer, CloudSiteSerializer


class GridSiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GridSite.objects.all()
    serializer_class = GridSiteSerializer
    template_name = 'gridsites.html'

    def retrieve(self, request, pk=None):
        last_fetched = GridSite.objects.aggregate(Max('fetched'))['fetched__max']
        # If there's no data then last_fetched is None.
        if last_fetched is not None:
            print last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20)
        if last_fetched is None or last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)):
            print 'Out of date'
            fetchset = VSuperSummaries.objects.using('grid').raw("SELECT Site, max(LatestEndTime) AS LatestPublish FROM VSuperSummaries WHERE Year=2019 GROUP BY 1;")
            for f in fetchset:
                GridSite.objects.update_or_create(defaults={'updated': f.LatestPublish}, name=f.Site)
        else:
            print 'No need to update'

        response = super(GridSiteViewSet, self).retrieve(request)
        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            # Single result put in list to work with same HTML template.
            response.data = {'sites': [response.data], 'last_fetched': last_fetched}

        response.data['returncode'] = 3
        response.data['stdout'] = "UNKNOWN"

        return response


class CloudSiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CloudSite.objects.all()
    serializer_class = CloudSiteSerializer
    template_name = 'cloudsites.html'

    def list(self, request):
        last_fetched = CloudSite.objects.aggregate(Max('fetched'))['fetched__max']
        print last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20)
        if last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)):
            print 'Out of date'
            fetchset =  VAnonCloudRecord.objects.using('cloud').raw("SELECT b.SiteName, COUNT(DISTINCT VMUUID) as VMs, CloudType, b.UpdateTime FROM (SELECT SiteName, MAX(UpdateTime) AS latest FROM VAnonCloudRecords WHERE UpdateTime>'2018-07-25' GROUP BY SiteName) AS a INNER JOIN VAnonCloudRecords AS b ON b.SiteName = a.SiteName AND b.UpdateTime = a.latest GROUP BY SiteName")
            for f in fetchset:
                CloudSite.objects.update_or_create(defaults={'vms': f.VMs, 'script': f.CloudType, 'updated': f.UpdateTime}, name=f.SiteName)
        else:
            print 'No need to update'

        response = super(CloudSiteViewSet, self).list(request)
        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {'sites': response.data, 'last_fetched': last_fetched}
        return response

    def retrieve(self, request, pk=None):
        last_fetched = CloudSite.objects.aggregate(Max('fetched'))['fetched__max']
        print last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20)
        if last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)):
            print 'Out of date'
            fetchset =  VAnonCloudRecord.objects.using('cloud').raw("SELECT b.SiteName, COUNT(DISTINCT VMUUID) as VMs, CloudType, b.UpdateTime FROM (SELECT SiteName, MAX(UpdateTime) AS latest FROM VAnonCloudRecords WHERE UpdateTime>'2018-07-25' GROUP BY SiteName) AS a INNER JOIN VAnonCloudRecords AS b ON b.SiteName = a.SiteName AND b.UpdateTime = a.latest GROUP BY SiteName")
            for f in fetchset:
                CloudSite.objects.update_or_create(defaults={'vms': f.VMs, 'script': f.CloudType, 'updated': f.UpdateTime}, name=f.SiteName)
        else:
            print 'No need to update'

        response = super(CloudSiteViewSet, self).retrieve(request)
        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            # Single result put in list to work with same HTML template.
            response.data = {'sites': [response.data], 'last_fetched': last_fetched}

        response.data['returncode'] = 3
        response.data['stdout'] = "UNKNOWN"

        return response
