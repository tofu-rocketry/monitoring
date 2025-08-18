from django.shortcuts import render
from datetime import datetime, timedelta

from django.db.models import Max

from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer


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

        response = super(BenchmarksViewSet, self).list(request)

        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {
                'benchmarks': response.data,
                'last_fetched': last_fetched
            }

        return response
