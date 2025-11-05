from rest_framework import serializers

from monitoring.iris.models import IrisCloudAndGrid


class IrisCloudAndGridSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # output format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.
    UpdateTime = serializers.DateTimeField(format=None)

    class Meta:
        model = IrisCloudAndGrid
        fields = (
            'SiteName',
            'SourceType',
            'UpdateTime',
        )
