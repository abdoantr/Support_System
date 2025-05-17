from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Frontend URLs
    path('', include('apps.core.urls')),
    
    # API URLs
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/services/', include('apps.services.urls')),
    path('api/tickets/', include('apps.tickets.urls')),
    path('api/appointments/', include('apps.appointments.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/core/', include('apps.core.urls_api')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)