from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment, Refund, Invoice
from apps.accounts.tasks import send_ticket_notification

@receiver(post_save, sender=Payment)
def payment_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal handler to update invoice status when payment is created or updated
    """
    if instance.status == 'success':
        # Get total paid amount for this invoice
        from django.db.models import Sum
        total_paid = Payment.objects.filter(
            invoice=instance.invoice,
            status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Update invoice status if fully paid
        if total_paid >= instance.invoice.amount:
            if instance.invoice.status != Invoice.Status.PAID:
                instance.invoice.status = Invoice.Status.PAID
                instance.invoice.save(update_fields=['status'])
                
                # Send notification to user
                if instance.invoice.user:
                    try:
                        send_ticket_notification.delay(
                            user_id=instance.invoice.user.id,
                            ticket_id=instance.invoice.id if instance.invoice.ticket else None,
                            notification_type='payment_received',
                            extra_context={'invoice_id': instance.invoice.id}
                        )
                    except:
                        # Task may fail if Celery is not running
                        pass

@receiver(post_save, sender=Refund)
def refund_updated(sender, instance, created, **kwargs):
    """
    Signal handler to handle refund status changes
    """
    # Check if refund was completed
    if instance.status == 'completed' and instance.processed_at:
        payment = instance.payment
        invoice = payment.invoice
        
        # Get total refunded amount
        from django.db.models import Sum
        total_refunded = Refund.objects.filter(
            payment=payment,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # If all the payment amount is refunded, revert invoice status
        if total_refunded >= payment.amount and invoice.status == Invoice.Status.PAID:
            # Change invoice status back to pending
            invoice.status = Invoice.Status.PENDING
            invoice.save(update_fields=['status'])
            
            # Send notification to user
            if invoice.user:
                try:
                    send_ticket_notification.delay(
                        user_id=invoice.user.id,
                        ticket_id=invoice.id if invoice.ticket else None,
                        notification_type='payment_refunded',
                        extra_context={'invoice_id': invoice.id}
                    )
                except:
                    # Task may fail if Celery is not running
                    pass 