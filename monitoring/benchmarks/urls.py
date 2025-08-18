from django.urls import path

from monitoring.benchmarks import views

urlpatterns = [
    path('', views.BenchmarksViewSet),
]