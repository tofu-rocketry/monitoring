from rest_framework import routers

from monitoring.benchmarks import views

router = routers.SimpleRouter()
router.register('', views.BenchmarksViewSet)

urlpatterns = router.urls
