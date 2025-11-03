from django.db import models


class IrisCloudGrid(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    SiteName = models.CharField(max_length=255)
    SourceType = models.CharField(max_length=50)
    UpdateTime = models.DateTimeField()

    class Meta:
        ordering = ('SiteName',)
        # unique_together = ('SiteName', 'SourceType')

class VSuperSummaries(models.Model):
    Site = models.CharField(max_length=255, primary_key=True)
    UpdateTime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'VSuperSummaries'
        verbose_name = 'Grid site'


class VAnonCloudRecords(models.Model):
    Site = models.CharField(max_length=255, primary_key=True)
    UpdateTime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'VAnonCloudRecords'
        verbose_name = 'Cloud site'
