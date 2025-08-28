from django.urls import path

from monitoring.availability import views

urlpatterns = [
    path('', views.status, name='availability'),
]
