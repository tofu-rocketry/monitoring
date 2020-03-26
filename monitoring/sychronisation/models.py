# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class GridSite(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, primary_key=True)
    updated = models.DateTimeField()


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
