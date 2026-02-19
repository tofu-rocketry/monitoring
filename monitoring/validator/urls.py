from django.urls import path

from monitoring.validator import views

urlpatterns = [
    path('', views.index, name="validator"),
]
