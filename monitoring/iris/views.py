from datetime import datetime, timedelta

from django.db.models import Max
from django.db.models.functions import Lower
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.renderers import TemplateHTMLRenderer

from monitoring.iris.models import IrisCloudAndGrid
from monitoring.iris.serializers import IrisCloudAndGridSerializer

from monitoring.publishing.views import update_dict_stdout_and_returncode


class IrisViewSet(viewsets.ReadOnlyModelViewSet):
    # Lower('SiteName'): sorts sites alphabetically, case-insensitively.
    # '-SourceType': reverse order: grid before cloud
    # '-UpdateTime': sorts records within each site by UpdateTime in descending order (latest first).
    queryset = IrisCloudAndGrid.objects.all().order_by(Lower('SiteName'), '-SourceType', '-UpdateTime')

    serializer_class = IrisCloudAndGridSerializer
    template_name = 'iris_cloud_and_grid.html'

    def list(self, request):
        last_fetched = IrisCloudAndGrid.objects.aggregate(Max('fetched'))['fetched__max']

        final_response = []
        response = super(IrisViewSet, self).list(request)

        for single_dict in response.data:
            date = single_dict.get('UpdateTime').replace(tzinfo=None)
            single_dict = update_dict_stdout_and_returncode(single_dict, date)
            final_response.append(single_dict)

        if type(request.accepted_renderer) is TemplateHTMLRenderer:
            response.data = {
                'irisCloudAndGridData': final_response,
                'last_fetched': last_fetched,
            }

        return response
