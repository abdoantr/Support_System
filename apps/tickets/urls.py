from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter
from . import views

app_name = 'tickets'

# Primary router
router = DefaultRouter()
router.register(r'tickets', views.TicketViewSet, basename='ticket')
router.register(r'comments', views.TicketCommentViewSet, basename='comment')

# Nested router for attachments
tickets_router = NestedSimpleRouter(router, r'tickets', lookup='ticket')
tickets_router.register(r'attachments', views.TicketAttachmentViewSet, basename='ticket-attachment')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(tickets_router.urls)),
]