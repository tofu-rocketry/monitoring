from rest_framework import routers

from monitoring.iris import views

router = routers.SimpleRouter()
router.register('', views.IrisViewSet)

urlpatterns = router.urls
