# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Sum

from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer

from models import GridSiteSync, VSuperSummaries, VSyncRecords
from serializers import GridSiteSyncSerializer


class GridSiteSyncViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GridSiteSync.objects.all()
    serializer_class = GridSiteSyncSerializer
    template_name = 'gridsites.html'

    def retrieve(self, request, pk=None):
        last_fetched = GridSiteSync.objects.aggregate(Max('fetched'))['fetched__max']
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

        response = super(GridSiteSyncViewSet, self).retrieve(request)
        date = response.data['updated'].replace(tzinfo=None)

        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            # Single result put in list to work with same HTML template.
            response.data = {'sites': [response.data], 'last_fetched': last_fetched}

        diff = datetime.today() - date
        if diff <= timedelta(days=7):
            response.data['returncode'] = 0
            response.data['stdout'] = "OK [ last published %s days ago: %s ]" % (diff.days, date.strftime("%Y-%m-%d"))
        elif diff > timedelta(days=7):
            response.data['returncode'] = 1
            response.data['stdout'] = "WARNING [ last published %s days ago: %s ]" % (diff.days, date.strftime("%Y-%m-%d"))
        else:
            response.data['returncode'] = 3
            response.data['stdout'] = "UNKNOWN"

        return response
