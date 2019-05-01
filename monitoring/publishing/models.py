# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class GridSite(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, primary_key=True)
    updated = models.DateTimeField()


class CloudSite(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, primary_key=True)
    vms = models.IntegerField(default=0)
    script = models.CharField(max_length=255)
    updated = models.DateTimeField()

    class Meta:
        ordering = ('name',)


class VAnonCloudRecord(models.Model):
    SiteName = models.CharField(max_length=255, primary_key=True)
    VMs = models.IntegerField()
    CloudType = models.CharField(max_length=255)
    UpdateTime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'vanoncloudrecords'

    def __str__(self):
        return '%s running "%s" updated at %s with %s records' % (
                                                    self.SiteName,
                                                    self.CloudType,
                                                    self.UpdateTime,
                                                    self.VMs)
