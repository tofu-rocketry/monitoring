from rest_framework import serializers

from models import CloudSite

class CloudSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CloudSite
        fields = ('name', 'script', 'updated')
