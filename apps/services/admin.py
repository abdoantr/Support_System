from django.contrib import admin
from .models import Service, ServiceFeature

# Register your models here.

@admin.register(ServiceFeature)
class ServiceFeatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_featured', 'is_active']
    list_filter = ['category', 'is_featured', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['features']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        (None, {
            'fields': ['name', 'description', 'category', 'image']
        }),
        ('Pricing', {
            'fields': ['price', 'price_period']
        }),
        ('Features', {
            'fields': ['features']
        }),
        ('Status', {
            'fields': ['is_featured', 'is_active']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
