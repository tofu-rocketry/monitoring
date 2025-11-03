from django.shortcuts import render
from datetime import datetime, timedelta

from django.db.models import Max
from django.db.models.functions import Lower

from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer


from monitoring.iris.models import IrisCloudGrid

from monitoring.iris.serializers import IrisCloudGridSerializer

class IrisViewSet(viewsets.ReadOnlyModelViewSet):
    # Lower('SiteName'): sorts sites alphabetically, case-insensitively.
    # '-UpdateTime': sorts records within each site by UpdateTime in descending order (latest first).
    queryset = IrisCloudGrid.objects.all().order_by(Lower('SiteName'), '-UpdateTime')

    serializer_class = IrisCloudGridSerializer
    template_name = 'iris_cloud_grid.html'

    def list(self, request):
        last_fetched = IrisCloudGrid.objects.aggregate(Max('fetched'))['fetched__max']
        if last_fetched is not None:
            print(last_fetched.replace(tzinfo=None), datetime.today() - timedelta(hours=1, seconds=20))

        response = super(IrisViewSet, self).list(request)

        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {
                'irisCloudGridData': response.data,
                'last_fetched': last_fetched,
            }

        return response

