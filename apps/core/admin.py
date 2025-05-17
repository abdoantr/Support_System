from django.contrib import admin
from .models import Profile, FAQ, FAQInteraction, UserSettings

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'phone', 'preferred_contact_method', 'is_available')
    search_fields = ('user__email', 'user__username', 'company', 'phone')
    list_filter = ('preferred_contact_method', 'is_available')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_published', 'order')
    list_filter = ('category', 'is_published')
    search_fields = ('question', 'answer')
    list_editable = ('is_published', 'order')

@admin.register(FAQInteraction)
class FAQInteractionAdmin(admin.ModelAdmin):
    list_display = ('faq', 'interaction_type', 'user', 'created_at')
    list_filter = ('interaction_type', 'created_at')
    search_fields = ('faq__question', 'user__email')
    date_hierarchy = 'created_at'

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
