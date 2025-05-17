from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')
router.register(r'time-slots', views.TimeSlotViewSet, basename='timeslot')
router.register(r'schedules', views.TechnicianScheduleViewSet, basename='schedule')

app_name = 'appointments'

urlpatterns = [
    path('', include(router.urls)),
] 