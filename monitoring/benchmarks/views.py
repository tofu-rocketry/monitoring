from django.shortcuts import render
from datetime import datetime, timedelta

from django.db.models import Max, Count
from django.db.models.functions import Lower

from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer


from monitoring.benchmarks.models import BenchmarksBySubmithost

from monitoring.benchmarks.serializers import BenchmarksBySubmithostSerializer

class BenchmarksViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BenchmarksBySubmithost.objects.all().order_by(Lower('SiteName'))

    serializer_class = BenchmarksBySubmithostSerializer
    template_name = 'benchmarks_by_submithost.html'

    def list(self, request):
        last_fetched = BenchmarksBySubmithost.objects.aggregate(Max('fetched'))['fetched__max']
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        response = super(BenchmarksViewSet, self).list(request)

        # Count number of distinct sites per RecordType
        site_counts_by_record_type = (
            BenchmarksBySubmithost.objects
            .values('RecordType')
            .annotate(site_count=Count('SiteName', distinct=True))
            .order_by('RecordType')
        )

        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {
                'benchmarks': response.data,
                'last_fetched': last_fetched,
                'site_counts_by_record_type': site_counts_by_record_type
            }

        return response
