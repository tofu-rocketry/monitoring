from django.conf.urls import include, url

from rest_framework import routers

from monitoring.synchronisation import views

router = routers.SimpleRouter()
router.register(r'grid', views.GridSiteSyncViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
]
