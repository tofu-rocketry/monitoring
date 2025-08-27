from django.conf.urls import url

from monitoring.availability import views

urlpatterns = [
    url(r'^$', views.status, name='availability'),
]
