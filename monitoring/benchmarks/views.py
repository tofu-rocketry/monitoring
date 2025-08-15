from django.shortcuts import render
from datetime import datetime, timedelta

from django.db.models import Max
from django.shortcuts import get_object_or_404
import pandas as pd

from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


from monitoring.benchmarks.models import BenchmarksBySubmithost

from monitoring.benchmarks.serializers import BenchmarksBySubmithostSerializer

class BenchmarksViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BenchmarksBySubmithost.objects.all()
    serializer_class = BenchmarksBySubmithostSerializer
    template_name = 'benchmarks_by_submithost.html'
    lookup_field = 'SiteName'

    def list(self, request):
        last_fetched = BenchmarksBySubmithost.objects.aggregate(Max('fetched'))['fetched__max']
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        final_response = []
        response = super(BenchmarksViewSet, self).list(request)

        for single_dict in response.data:
            date = single_dict.get('UpdateTime').replace(tzinfo=None)
            final_response.append(date)

        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {
                'benchmarks': final_response,
                'last_fetched': last_fetched
            }

        return response

    def retrieve(self, request, SiteName=None):
        last_fetched = BenchmarksBySubmithost.objects.aggregate(Max('fetched'))['fetched__max']
        # If there's no data then last_fetched is None.
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))
        
        final_response = []
        sites_list_qs = BenchmarksBySubmithost.objects.filter(SiteName=SiteName)
        sites_list_serializer = self.get_serializer(sites_list_qs, many=True)
        
        for single_dict in sites_list_serializer.data:
            date = single_dict.get('UpdateTime').replace(tzinfo=None)
            final_response.append(date)

        # Wrap data in a dict so that it can display in template.
        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            # Single result put in list to work with same HTML template.
            response = {
                'benchmarks': final_response,
                'last_fetched': last_fetched
            }

        return Response(response)
