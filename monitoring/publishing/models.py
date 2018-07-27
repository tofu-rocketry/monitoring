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
