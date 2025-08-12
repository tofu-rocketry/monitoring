from django.db import models

class BenchmarksBySubmithost(models.Model):
    fetched = models.DateTimeField(auto_now=True)
    SiteName = models.CharField(max_length=255)
    SubmitHost = models.CharField(max_length=255)
    ServiceLevelType = models.DecimalField(max_digits=10, decimal_places=3)
    ServiceLevel = models.CharField(max_length=50)
    SourceView = models.CharField(max_length=50)
    UpdateTime = models.DateTimeField()

    class Meta:
        ordering = ('SiteName',)
