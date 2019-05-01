from rest_framework import serializers

from models import CloudSite


class GridSiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CloudSite
        fields = ('url', 'name', 'updated')


class CloudSiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CloudSite
        fields = ('url', 'name', 'vms', 'script', 'updated')
