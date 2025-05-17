from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import models
from .models import Invoice, Payment, Refund
from apps.accounts.serializers import UserSerializer
from apps.services.serializers import ServiceSerializer
from apps.tickets.serializers import TicketSerializer
from apps.accounts.models import User
from apps.services.models import Service
from apps.tickets.models import Ticket
from django.utils import timezone

class InvoiceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        write_only=True,
        required=False,
        queryset=User.objects.filter(is_active=True)
    )
    ticket = TicketSerializer(read_only=True)
    ticket_id = serializers.PrimaryKeyRelatedField(
        source='ticket',
        write_only=True,
        required=False,
        allow_null=True,
        queryset=Ticket.objects.all()
    )
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        source='service',
        write_only=True,
        required=False,
        allow_null=True,
        queryset=Service.objects.filter(is_active=True)
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'user', 'user_id', 'ticket', 'ticket_id', 'service', 'service_id',
            'amount', 'status', 'status_display', 'due_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_due_date(self, value):
        """Validate due date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError(_("Due date cannot be in the past"))
        return value
    
    def validate(self, data):
        """Ensure either a ticket or service is provided"""
        ticket = data.get('ticket')
        service = data.get('service')
        
        if not ticket and not service:
            raise serializers.ValidationError(_("Either a ticket or service must be specified"))
        
        return data

class PaymentSerializer(serializers.ModelSerializer):
    invoice = InvoiceSerializer(read_only=True)
    invoice_id = serializers.PrimaryKeyRelatedField(
        source='invoice',
        write_only=True,
        queryset=Invoice.objects.exclude(status='paid')
    )
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'invoice_id', 'amount', 'method', 'method_display',
            'transaction_id', 'payment_date', 'status', 'status_display', 'notes'
        ]
        read_only_fields = ['payment_date']
    
    def validate(self, data):
        """Validate payment amount against invoice amount"""
        invoice = data.get('invoice')
        amount = data.get('amount')
        
        if invoice and amount:
            # Get total amount already paid for this invoice
            paid_amount = Payment.objects.filter(
                invoice=invoice,
                status='success'
            ).exclude(id=self.instance.id if self.instance else None).aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            
            # Check if this payment would exceed the invoice amount
            if paid_amount + amount > invoice.amount:
                raise serializers.ValidationError(
                    _("Payment amount would exceed the remaining balance")
                )
                
            # Check if invoice is already paid or cancelled
            if invoice.status in ['paid', 'cancelled']:
                raise serializers.ValidationError(
                    _("Cannot make payment on an invoice that is already paid or cancelled")
                )
        
        return data

class RefundSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer(read_only=True)
    payment_id = serializers.PrimaryKeyRelatedField(
        source='payment',
        write_only=True,
        queryset=Payment.objects.filter(status='success')
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'payment_id', 'amount', 'reason', 'status',
            'status_display', 'processed_at', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['processed_at', 'created_at', 'updated_at']
    
    def validate_amount(self, value):
        """Validate refund amount doesn't exceed payment amount"""
        payment = self.initial_data.get('payment')
        if payment and value > payment.amount:
            raise serializers.ValidationError(
                _("Refund amount cannot exceed the payment amount")
            )
        return value 