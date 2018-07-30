# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class CloudSite(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, primary_key=True)
    script = models.CharField(max_length=255)
    updated = models.DateTimeField()

    class Meta:
        ordering = ('name',)


class VAnonCloudRecord(models.Model):
    SiteName = models.CharField(max_length=255, primary_key=True)
    CloudType = models.CharField(max_length=255)
    UpdateTime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'vanoncloudrecords'

    def __str__(self):
        return '%s, running "%s", updated at %s' % (self.SiteName,
                                                    self.CloudType,
                                                    self.UpdateTime)
