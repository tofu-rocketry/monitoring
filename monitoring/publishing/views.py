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
    VSuperSummaries,
    CloudSite,
    GridSiteSync,
    VSyncRecords,
    GridSiteSyncSubmitH
)

from monitoring.publishing.serializers import (
    GridSiteSerializer,
    CloudSiteSerializer,
    GridSiteSyncSerializer,
    GridSiteSyncSubmitHSerializer
)

summaries_dict_standard = {
    "Site": [],
    "Month": [],
    "Year": [],
    "RecordCountPublished": [],
    "RecordStart": [],
    "RecordEnd": [],
    "SubmitHostSumm": [],
}

syncrecords_dict_standard = {
    "Site": [],
    "Month": [],
    "Year": [],
    "RecordCountInDb": [],
    "SubmitHostSync": []
}


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


def fill_summaries_dict(inpDict, row):

    fields_to_update_and_value_to_add = {
        "Site": row.Site,
        "Month": row.Month,
        "Year": row.Year,
        "RecordCountPublished": row.RecordCountPublished,
        "RecordStart": row.RecordStart,
        "RecordEnd": row.RecordEnd,
    }

    for field, value in fields_to_update_and_value_to_add.items():
        inpDict[field] = inpDict.get(field) + [value]

    if hasattr(row, "SubmitHostSumm"):
        inpDict["SubmitHostSumm"] = inpDict.get("SubmitHostSumm") + [row.SubmitHostSumm]

    return inpDict


def fill_syncrecords_dict(inpDict, row):
    inpDict["Site"] = inpDict.get("Site") + [row.Site]
    inpDict["Month"] = inpDict.get("Month") + [row.Month]
    inpDict["Year"] = inpDict.get("Year") + [row.Year]
    inpDict["RecordCountInDb"] = inpDict.get("RecordCountInDb") + [row.RecordCountInDb]
    if hasattr(row, "SubmitHostSync"):
        inpDict["SubmitHostSync"] = inpDict.get("SubmitHostSync") + [row.SubmitHostSync]
    return inpDict


def correct_dict(inpDict):
    keys_to_remove = []
    for key, val in inpDict.items():
        if len(val) == 0:
            keys_to_remove.append(key)
    for key in keys_to_remove:
        inpDict.pop(key)
    return inpDict


def determine_sync_status(f):
    RecordCountPublished = f.get("RecordCountPublished")
    RecordCountInDb = f.get("RecordCountInDb")
    rel_diff1 = abs(RecordCountPublished - RecordCountInDb)/RecordCountInDb
    rel_diff2 = abs(RecordCountPublished - RecordCountInDb)/RecordCountPublished
    if rel_diff1 < 0.01 or rel_diff2 < 0.01:
        syncstatus = "OK"
    else:
        syncstatus = "ERROR [ Please use the Gap Publisher to synchronise this dataset]"
    return syncstatus


# Combine Year and Month into one string (display purposes)
def get_year_month_str(year, month):
    year_string = str(year)
    month_string = str(month)
    if len(month_string) == 1:
        month_string = '0' + month_string
    return year_string + '-' + month_string


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
    page_size = 1000 # Number of items to be fetched per page


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
        Year, Month = YearMonth.split('-')
        sitename_in_table = None
        yearmonth_in_table = None

        # This is to ensure the data is updated when changing month
        if GridSiteSyncSubmitH.objects.count() > 0:
            row_1 = GridSiteSyncSubmitH.objects.filter()[:1].get()
            sitename_in_table = row_1.SiteName
            yearmonth_in_table = row_1.YearMonth

        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))
        if last_fetched is None or last_fetched.replace(tzinfo=None) < (datetime.today() - timedelta(hours=1, seconds=20)) or (sitename_in_table != SiteName) or (yearmonth_in_table != YearMonth):
            print('Out of date')

            sql_query_summaries = """
                SELECT
                    Site,
                    Month,
                    Year,
                    SUM(NumberOfJobs) AS RecordCountPublished,
                    SubmitHost AS SubmitHostSumm,
                    MIN(EarliestEndTime) AS RecordStart,
                    MAX(LatestEndTime) AS RecordEnd
                FROM VSuperSummaries
                WHERE
                    Site='{}' AND
                    Month='{}' AND
                    Year='{}'
                GROUP BY SubmitHost;
            """.format(SiteName, Month, Year)
            fetchset_Summaries = VSuperSummaries.objects.using('grid').raw(sql_query_summaries)

            sql_query_syncrecords = """
                SELECT
                    Site,
                    Month,
                    Year,
                    SUM(NumberOfJobs) AS RecordCountInDb,
                    SubmitHost AS SubmitHostSync
                FROM VSyncRecords
                WHERE
                    Site='{}' AND
                    Month='{}' AND
                    Year='{}'
                GROUP BY SubmitHost;
            """.format(SiteName, Month, Year)
            fetchset_SyncRecords = VSyncRecords.objects.using('grid').raw(sql_query_syncrecords)

            summaries_dict = summaries_dict_standard.copy()
            syncrecords_dict = syncrecords_dict_standard.copy()

            for row in fetchset_Summaries:
                summaries_dict = fill_summaries_dict(summaries_dict, row)
                summaries_dict = correct_dict(summaries_dict)
            for row in fetchset_SyncRecords:
                syncrecords_dict = fill_syncrecords_dict(syncrecords_dict, row)
                syncrecords_dict = correct_dict(syncrecords_dict)

            df_Summaries = pd.DataFrame.from_dict(summaries_dict)
            df_SyncRecords = pd.DataFrame.from_dict(syncrecords_dict)
            df_Summaries.dropna(inplace=True)
            df_SyncRecords.dropna(inplace=True)

            df_all = df_Summaries.merge(
                df_SyncRecords,
                left_on=['Site', 'Month', 'Year', 'SubmitHostSumm'],
                right_on=['Site', 'Month', 'Year', 'SubmitHostSync'],
                how='outer'
            )

            fetchset = df_all.to_dict('index')

            # This is to list only data for one month
            GridSiteSyncSubmitH.objects.all().delete()

            for f in fetchset.values():
                GridSiteSyncSubmitH.objects.update_or_create(
                    defaults={
                        'RecordStart': f.get("RecordStart"),
                        'RecordEnd': f.get("RecordEnd"),
                        'RecordCountPublished': f.get("RecordCountPublished"),
                        'RecordCountInDb': f.get("RecordCountInDb"),
                    },
                    SiteName=f.get("Site"),
                    YearMonth=get_year_month_str(f.get("Year"), f.get("Month")),
                    Month=f.get("Month"),
                    Year=f.get("Year"),
                    SubmitHost=f.get("SubmitHostSumm"),
                )

        else:
            print('No need to update')

        response = super(GridSiteSyncSubmitHViewSet, self).list(request)
        response.data = {
            'submisthosts': response.data,
            'last_fetched': last_fetched
        }
        return response


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
