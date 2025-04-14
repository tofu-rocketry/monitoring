from rest_framework import serializers
from rest_framework.reverse import reverse

from monitoring.publishing.models import (
    CloudSite,
    GridSite,
    GridSiteSync,
    GridSiteSyncSubmitH
)


class GridSiteSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.
    updated = serializers.DateTimeField(format=None)

    class Meta:
        model = GridSite
        fields = (
            'url',
            'SiteName',
            'updated'
        )

        # Sitename substitutes for pk
        lookup_field = 'SiteName'
        extra_kwargs = {
            'url': {'view_name': 'gridsite-detail', 'lookup_field': 'SiteName'}
        }


class GridSiteSyncSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.

    class Meta:
        model = GridSiteSync
        fields = (
            'url',
            'SiteName',
            'YearMonth',
            'RecordStart',
            'RecordEnd',
            'RecordCountPublished',
            'RecordCountInDb',
            'SyncStatus'
        )

        # Sitename substitutes for pk
        lookup_field = 'SiteName'
        extra_kwargs = {
            'url': {'view_name': 'gridsitesync-detail', 'lookup_field': 'SiteName'}
        }


class CloudSiteSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.
    updated = serializers.DateTimeField(format=None)

    class Meta:
        model = CloudSite
        fields = (
            'url',
            'SiteName',
            'Vms',
            'Script',
            'updated'
        )

        # Sitename substitutes for pk
        lookup_field = 'SiteName'
        extra_kwargs = {
            'url': {'view_name': 'cloudsite-detail', 'lookup_field': 'SiteName'}
        }


class MultipleFieldLookup(serializers.HyperlinkedIdentityField):
    # HyperlinkedModelSerializer seems to NOT able to work with two lookup_fields
    # This class is ONLY capable to match object instance to its URL representation.
    # i.e, `SiteName` and `YearMonth` ONLY
    #
    # Overriding the get_url() method - To match object instance to its URL representation.
    def get_url(self, obj, view_name, request, format):
        if not obj.SiteName or not obj.YearMonth:
            return None

        return request.build_absolute_uri(
            reverse(
                view_name,
                kwargs={
                    'SiteName': obj.SiteName,
                    'YearMonth': obj.YearMonth
                },
                request=request,
                format=format
            ))


class GridSiteSyncSubmitHSerializer(serializers.HyperlinkedModelSerializer):
    # Override default format with None so that Python datetime is used as
    # ouput format. Encoding will be determined by the renderer and can be
    # formatted by a template filter.

    # This helps us to match or construct the absolute URL based on the `SiteName` and `YearMonth`
    url = MultipleFieldLookup(view_name='gridsync-submithost')

    class Meta:
        model = GridSiteSyncSubmitH
        fields = (
            'url',
            'SiteName',
            'YearMonth',
            'RecordStart',
            'RecordEnd',
            'RecordCountPublished',
            'RecordCountInDb',
            'SubmitHost'
        )
