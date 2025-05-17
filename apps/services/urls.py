from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'services'

router = DefaultRouter()
router.register('features', views.ServiceFeatureViewSet)
router.register('', views.ServiceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
