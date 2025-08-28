from django.urls import include, path

from rest_framework import routers

from monitoring.synchronisation import views

router = routers.SimpleRouter()
router.register(r'grid', views.GridSiteSyncViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
