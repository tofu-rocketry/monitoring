from rest_framework import serializers

from models import GridSiteSync


class GridSiteSyncSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.
    updated = serializers.DateTimeField(format=None)

    class Meta:
        model = GridSiteSync
        fields = ('url', 'site', 'year', 'month',
                  'site_count', 'repository_count', 'difference')
