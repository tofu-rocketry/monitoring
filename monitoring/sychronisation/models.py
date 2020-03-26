# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class GridSiteSync(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    site = models.CharField(max_length=255, primary_key=True)
    year = models.IntegerField(primary_key=True)
    month = models.IntegerField(primary_key=True)
    site_count = models.IntegerField()
    repository_count = models.IntegerField()


class VSuperSummaries(models.Model):
    Site = models.CharField(max_length=255, primary_key=True)
    Year = models.IntegerField(primary_key=True)
    Month = models.IntegerField(primary_key=True)
    NumberOfJobs = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'VSuperSummaries'


class VSyncRecords(models.Model):
    Site = models.CharField(max_length=255, primary_key=True)
    Year = models.IntegerField(primary_key=True)
    Month = models.IntegerField(primary_key=True)
    NumberOfJobs = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'VSyncRecords'
