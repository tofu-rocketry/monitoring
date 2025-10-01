# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.db.models import Max
from django.shortcuts import get_object_or_404
import pandas as pd

from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


from monitoring.publishing.models import (
    GridSite,
    CloudSite,
    GridSiteSync,
    GridSiteSyncSubmitH
)

from monitoring.publishing.serializers import (
    GridSiteSerializer,
    CloudSiteSerializer,
    GridSiteSyncSerializer,
    GridSiteSyncSubmitHSerializer
)


def update_dict_stdout_and_returncode(single_dict, date):
    diff = datetime.today() - date
    date = date.strftime("%Y-%m-%d")

    if diff <= timedelta(days=7):
        single_dict['returncode'] = 0
        single_dict['stdout'] = "OK [ last published %s days ago: %s ]" % (diff.days, date)
    elif diff > timedelta(days=7):
        single_dict['returncode'] = 1
        single_dict['stdout'] = "WARNING [ last published %s days ago: %s ]" % (diff.days, date)
    else:
        single_dict['returncode'] = 3
        single_dict['stdout'] = "UNKNOWN"
    return single_dict


class GridSiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GridSite.objects.all()
    serializer_class = GridSiteSerializer
    template_name = 'gridsites.html'
    lookup_field = 'SiteName'

    def list(self, request):
        last_fetched = GridSite.objects.aggregate(Max('fetched'))['fetched__max']
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        final_response = []
        response = super(GridSiteViewSet, self).list(request)

        for single_dict in response.data:
            date = single_dict.get('updated').replace(tzinfo=None)
            single_dict = update_dict_stdout_and_returncode(single_dict, date)
            final_response.append(single_dict)

        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {
                'sites': final_response,
                'last_fetched': last_fetched
            }

        return response

    def retrieve(self, request, SiteName=None):
        last_fetched = GridSite.objects.aggregate(Max('fetched'))['fetched__max']
        # If there's no data then last_fetched is None.
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        response = super(GridSiteViewSet, self).retrieve(request)
        date = response.data['updated'].replace(tzinfo=None)
        response.data = update_dict_stdout_and_returncode(response.data, date)

        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            # Single result put in list to work with same HTML template.
            response.data = {
                'sites': [response.data],
                'last_fetched': last_fetched
            }

        return response


class GridSiteSyncPagination(PageNumberPagination):
    page_size = 1000  # Number of items to be fetched per page


class GridSiteSyncViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GridSiteSync.objects.all()
    serializer_class = GridSiteSyncSerializer
    lookup_field = 'SiteName'
    pagination_class = GridSiteSyncPagination

    # When a single site is showed (retrieve function used), the template
    # is different than the one used when showing a list of sites
    def get_template_names(self):
        if self.action == 'list':
            return ['gridsync.html']
        elif self.action == 'retrieve':
            return ['gridsync_singlesite.html']

    def list(self, request):
        last_fetched = GridSiteSync.objects.aggregate(Max('fetched'))['fetched__max']

        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        response = super(GridSiteSyncViewSet, self).list(request)
        response.data = {
            'records': response.data,
            'last_fetched': last_fetched
        }
        return response

    def retrieve(self, request, SiteName=None):
        last_fetched = GridSiteSync.objects.aggregate(Max('fetched'))['fetched__max']

        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        sites_list_qs = GridSiteSync.objects.filter(SiteName=SiteName)
        sites_list_serializer = self.get_serializer(sites_list_qs, many=True)

        response = {
            'records': sites_list_serializer.data,
            'last_fetched': last_fetched
        }
        return Response(response)


# Needed for passing two parameters to a viewset (GridSiteSyncSubmitHViewSet)
class MultipleFieldLookupMixin:
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs.get(field):
                filter[field] = self.kwargs[field]
        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        return obj


class GridSiteSyncSubmitHViewSet(MultipleFieldLookupMixin, viewsets.ReadOnlyModelViewSet):
    queryset = GridSiteSyncSubmitH.objects.all()
    serializer_class = GridSiteSyncSubmitHSerializer
    template_name = 'gridsync_submithost.html'
    lookup_fields = ('SiteName', 'YearMonth')

    def list(self, request):
        last_fetched = GridSiteSyncSubmitH.objects.aggregate(Max('fetched'))['fetched__max']
        response = super(GridSiteSyncSubmitHViewSet, self).list(request)
        response.data = {
            'submisthosts': response.data,
            'last_fetched': last_fetched
        }
        return response

    def retrieve(self, request, SiteName=None, YearMonth=None):
        last_fetched = GridSiteSyncSubmitH.objects.aggregate(Max('fetched'))['fetched__max']

        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        sites_and_year_list_qs = GridSiteSyncSubmitH.objects.filter(
            SiteName=SiteName,
            YearMonth=YearMonth
        ).order_by('SubmitHost')

        sites_list_serializer = self.get_serializer(sites_and_year_list_qs, many=True)

        response = {
            'submisthosts': sites_list_serializer.data,
            'last_fetched': last_fetched
        }

        return Response(response)


class CloudSiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CloudSite.objects.all()
    serializer_class = CloudSiteSerializer
    template_name = 'cloudsites.html'
    lookup_field = 'SiteName'

    def list(self, request):
        last_fetched = CloudSite.objects.aggregate(Max('fetched'))['fetched__max']
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        response = super(CloudSiteViewSet, self).list(request)
        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {
                'sites': response.data,
                'last_fetched': last_fetched
            }
        return response

    def retrieve(self, request, SiteName=None):
        last_fetched = CloudSite.objects.aggregate(Max('fetched'))['fetched__max']
        print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        response = super(CloudSiteViewSet, self).retrieve(request)
        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            # Single result put in list to work with same HTML template.
            response.data = {
                'sites': [response.data],
                'last_fetched': last_fetched
            }

        response.data['returncode'] = 3
        response.data['stdout'] = "UNKNOWN"

        return response
