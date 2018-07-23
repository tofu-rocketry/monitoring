from rest_framework import serializers

from models import CloudSite

class CloudSiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CloudSite
        fields = ('url', 'name', 'script', 'updated')
