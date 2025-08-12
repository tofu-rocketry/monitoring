from rest_framework import routers

from monitoring.benchmarks import views
from django.urls import re_path

router = routers.SimpleRouter()
router.register(r'benchmarks', views.BenchmarksViewSet)

urlpatterns = [
    re_path(
        r'^benchmarks/(?P<SiteName>[a-zA-Z0-9._-]+)/$',
        views.BenchmarksViewSet.as_view({'get': 'retrieve'}),
        name='benchmarksbysubmithost-list'
    ),
]

urlpatterns += router.urls
