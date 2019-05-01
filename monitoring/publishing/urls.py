from django.conf.urls import include, url

from rest_framework import routers

import views

router = routers.SimpleRouter()
router.register(r'cloud', views.CloudSiteViewSet)
router.register(r'grid', views.GridSiteViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
]
