from rest_framework import routers
from django.urls import path, include

from monitoring.benchmarks import views

router = routers.SimpleRouter()
router.register('', views.BenchmarksViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
