from django.urls import include, path
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('availability/', include('monitoring.availability.urls')),
    path('publishing/', include('monitoring.publishing.urls')),
    path('benchmarks/', include('monitoring.benchmarks.urls')),
    path('iris/', include('monitoring.iris.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('validator/', include ('monitoring.validator.urls')),
]
