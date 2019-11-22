from rest_framework import serializers

from models import CloudSite, GridSite


class GridSiteSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.
    updated = serializers.DateTimeField(format=None)

    class Meta:
        model = GridSite
        fields = ('url', 'name', 'updated')


class CloudSiteSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.
    updated = serializers.DateTimeField(format=None)

    class Meta:
        model = CloudSite
        fields = ('url', 'name', 'vms', 'script', 'updated')
