from django.urls import include, path
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('availability/', include('monitoring.availability.urls')),
    path('publishing/', include('monitoring.publishing.urls')),
    path('benchmarks/', include('monitoring.benchmarks.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
