from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Invoice, Payment, Refund
from apps.accounts.models import User
from apps.tickets.models import Ticket
from apps.services.models import Service

class InvoiceForm(forms.ModelForm):
    """Form for creating and updating invoices"""
    
    class Meta:
        model = Invoice
        fields = ['user', 'ticket', 'service', 'amount', 'status', 'due_date', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        
        # Only active users
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        
        # Only active services
        self.fields['service'].queryset = Service.objects.filter(is_active=True)
        
        # Limit access based on user role
        if self.request_user and not self.request_user.is_staff:
            self.fields['user'].initial = self.request_user
            self.fields['user'].widget = forms.HiddenInput()
            
            # Only tickets owned by the user
            self.fields['ticket'].queryset = Ticket.objects.filter(user=self.request_user)
    
    def clean(self):
        cleaned_data = super().clean()
        ticket = cleaned_data.get('ticket')
        service = cleaned_data.get('service')
        due_date = cleaned_data.get('due_date')
        
        # Validate that either ticket or service is provided
        if not ticket and not service:
            raise forms.ValidationError(_("Either a ticket or service must be specified"))
        
        # Validate due date is not in the past
        if due_date and due_date < timezone.now().date():
            self.add_error('due_date', _("Due date cannot be in the past"))
        
        return cleaned_data

class PaymentForm(forms.ModelForm):
    """Form for creating and updating payments"""
    
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'method', 'transaction_id', 'status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        
        # Limit access based on user role
        if self.request_user and not self.request_user.is_staff:
            # Only invoices owned by the user
            self.fields['invoice'].queryset = Invoice.objects.filter(
                user=self.request_user,
                status='pending'
            )
            
            # Non-staff users cannot set status
            self.fields['status'].widget = forms.HiddenInput()
            self.fields['status'].initial = 'pending'
    
    def clean(self):
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        amount = cleaned_data.get('amount')
        
        if invoice and amount:
            # Check if invoice is already paid or cancelled
            if invoice.status in ['paid', 'cancelled']:
                raise forms.ValidationError(
                    _("Cannot make payment on an invoice that is already paid or cancelled")
                )
            
            # Get total amount already paid for this invoice
            from django.db.models import Sum
            paid_amount = Payment.objects.filter(
                invoice=invoice,
                status='success'
            ).exclude(id=self.instance.id if self.instance else None).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            # Check if this payment would exceed the invoice amount
            if paid_amount + amount > invoice.amount:
                self.add_error(
                    'amount',
                    _("Payment amount would exceed the remaining balance of %(balance)s") % {
                        'balance': invoice.amount - paid_amount
                    }
                )
        
        return cleaned_data

class RefundForm(forms.ModelForm):
    """Form for creating and updating refunds"""
    
    class Meta:
        model = Refund
        fields = ['payment', 'amount', 'reason', 'status', 'notes']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        
        # Only successful payments can be refunded
        self.fields['payment'].queryset = Payment.objects.filter(status='success')
        
        # Limit access based on user role
        if self.request_user and not self.request_user.is_staff:
            # Only payments for invoices owned by the user
            self.fields['payment'].queryset = self.fields['payment'].queryset.filter(
                invoice__user=self.request_user
            )
            
            # Non-staff users cannot set status
            self.fields['status'].widget = forms.HiddenInput()
            self.fields['status'].initial = 'pending'
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        payment = self.cleaned_data.get('payment')
        
        if payment and amount:
            # Check if amount exceeds payment amount
            if amount > payment.amount:
                raise forms.ValidationError(
                    _("Refund amount cannot exceed the payment amount of %(amount)s") % {
                        'amount': payment.amount
                    }
                )
                
            # Check if there are already refunds for this payment
            from django.db.models import Sum
            refunded_amount = Refund.objects.filter(
                payment=payment,
                status__in=['approved', 'completed']
            ).exclude(id=self.instance.id if self.instance else None).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            # Check if this refund would exceed the remaining amount
            if refunded_amount + amount > payment.amount:
                raise forms.ValidationError(
                    _("Refund amount would exceed the remaining refundable amount of %(amount)s") % {
                        'amount': payment.amount - refunded_amount
                    }
                )
        
        return amount 