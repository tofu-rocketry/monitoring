# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class GridSiteSync(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    site = models.CharField(max_length=255)
    year = models.IntegerField()
    month = models.IntegerField()
    site_count = models.IntegerField()
    repository_count = models.IntegerField()
    difference = models.IntegerField()

    class Meta:
        unique_together = ['site', 'year', 'month']


class VSuperSummaries(models.Model):
    Site = models.CharField(max_length=255)
    Year = models.IntegerField()
    Month = models.IntegerField()
    NumberOfJobs = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'VSuperSummaries'
        unique_together = ('Site', 'Year', 'Month')


class VSyncRecords(models.Model):
    Site = models.CharField(max_length=255)
    Year = models.IntegerField()
    Month = models.IntegerField()
    NumberOfJobs = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'VSyncRecords'
        unique_together = ('Site', 'Year', 'Month')
