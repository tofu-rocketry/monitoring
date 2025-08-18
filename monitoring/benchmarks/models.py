from django.db import models

class BenchmarksBySubmithost(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    SiteName = models.CharField(max_length=255)
    SubmitHost = models.CharField(max_length=255)
    ServiceLevelType = models.CharField(max_length=50)
    ServiceLevel = models.DecimalField(max_digits=10, decimal_places=3)
    SourceView = models.CharField(max_length=50)
    UpdateTime = models.DateTimeField()

    class Meta:
        ordering = ('SiteName',)

class VJobRecords(models.Model):
    Site = models.CharField(max_length=255, primary_key=True)
    SubmitHost = models.CharField(max_length=255)
    ServiceLevelType = models.CharField(max_length=50)
    ServiceLevel = models.DecimalField(max_digits=10, decimal_places=3)
    UpdateTime = models.DateTimeField()
    EndTime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'VJobRecords'
        verbose_name = 'Job Record'

class VSummaries(models.Model):
    Site = models.CharField(max_length=255, primary_key=True)
    SubmitHost = models.CharField(max_length=255)
    ServiceLevelType = models.CharField(max_length=50)
    ServiceLevel = models.DecimalField(max_digits=10, decimal_places=3)
    UpdateTime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'VSummaries'
        verbose_name = 'Summary'

class VNormalisedSummaries(models.Model):
    Site = models.CharField(max_length=255, primary_key=True)
    SubmitHost = models.CharField(max_length=255)
    ServiceLevelType = models.CharField(max_length=50)
    ServiceLevel = models.DecimalField(max_digits=10, decimal_places=3)
    UpdateTime = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'VNormalisedSummaries'
        verbose_name = 'Normalised Summary'                        
