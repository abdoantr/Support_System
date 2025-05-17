from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Invoice, Payment, Refund

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'ticket', 'amount', 'status', 'due_date', 'created_at')
    list_filter = ('status', 'due_date', 'created_at')
    search_fields = ('user__email', 'ticket__title', 'service__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'ticket', 'service', 'amount', 'status')
        }),
        (_('Dates'), {
            'fields': ('due_date', 'created_at', 'updated_at')
        }),
        (_('Additional Information'), {
            'fields': ('notes',)
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'amount', 'method', 'status', 'payment_date')
    list_filter = ('status', 'method', 'payment_date')
    search_fields = ('invoice__user__email', 'transaction_id')
    date_hierarchy = 'payment_date'
    readonly_fields = ('payment_date',)
    fieldsets = (
        (_('Payment Information'), {
            'fields': ('invoice', 'amount', 'method', 'status')
        }),
        (_('Transaction Information'), {
            'fields': ('transaction_id', 'payment_date', 'notes')
        }),
    )

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'amount', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'created_at', 'processed_at')
    search_fields = ('payment__invoice__user__email',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Refund Information'), {
            'fields': ('payment', 'amount', 'status', 'reason')
        }),
        (_('Processing Information'), {
            'fields': ('processed_at', 'created_at', 'updated_at', 'notes')
        }),
    ) 