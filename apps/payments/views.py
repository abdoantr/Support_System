from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Invoice, Payment, Refund
from .serializers import InvoiceSerializer, PaymentSerializer, RefundSerializer

class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or staff to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True
            
        # Otherwise, users can only access their own data
        return obj.user == request.user

class InvoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows invoices to be viewed or edited.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'service', 'ticket']
    search_fields = ['user__email', 'ticket__title', 'service__name']
    ordering_fields = ['created_at', 'due_date', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter invoices based on user role.
        Staff can see all invoices, regular users can only see their own.
        """
        user = self.request.user
        if user.is_staff:
            return Invoice.objects.all()
        return Invoice.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """
        Set the user to the current user if not specified.
        """
        if not serializer.validated_data.get('user'):
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    @extend_schema(
        description="Mark an invoice as paid",
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def mark_paid(self, request, pk=None):
        """
        Mark an invoice as paid (admin only).
        """
        invoice = self.get_object()
        
        if invoice.status == Invoice.Status.PAID:
            return Response(
                {"error": _("Invoice is already marked as paid")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if invoice.status == Invoice.Status.CANCELLED:
            return Response(
                {"error": _("Cannot mark a cancelled invoice as paid")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        invoice.status = Invoice.Status.PAID
        invoice.save(update_fields=['status'])
        
        return Response({"message": _("Invoice marked as paid successfully")})
    
    @extend_schema(
        description="Cancel an invoice",
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def cancel(self, request, pk=None):
        """
        Cancel an invoice (admin only).
        """
        invoice = self.get_object()
        
        if invoice.status == Invoice.Status.CANCELLED:
            return Response(
                {"error": _("Invoice is already cancelled")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if invoice.status == Invoice.Status.PAID:
            return Response(
                {"error": _("Cannot cancel a paid invoice")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        invoice.status = Invoice.Status.CANCELLED
        invoice.save(update_fields=['status'])
        
        return Response({"message": _("Invoice cancelled successfully")})
    
    @extend_schema(
        description="Get overdue invoices",
        responses={200: InvoiceSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def overdue(self, request):
        """
        Get all overdue invoices (admin only).
        """
        today = timezone.now().date()
        overdue_invoices = Invoice.objects.filter(
            status=Invoice.Status.PENDING,
            due_date__lt=today
        )
        
        page = self.paginate_queryset(overdue_invoices)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(overdue_invoices, many=True)
        return Response(serializer.data)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows payments to be viewed or edited.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'method', 'invoice']
    search_fields = ['transaction_id', 'invoice__user__email']
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']
    
    def get_queryset(self):
        """
        Filter payments based on user role.
        Staff can see all payments, regular users can only see payments for their invoices.
        """
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(invoice__user=user)
    
    def perform_create(self, serializer):
        """
        Set the payment status based on the method.
        For cash and bank transfers, the payment is pending until confirmed.
        For credit cards, the payment is successful immediately.
        """
        payment = serializer.save()
        
        # For credit cards, mark as successful immediately
        if payment.method == Payment.Method.CREDIT_CARD:
            payment.status = 'success'
            payment.save(update_fields=['status'])
            
            # Update invoice status if payment completes the invoice
            self._update_invoice_status(payment.invoice)
    
    def _update_invoice_status(self, invoice):
        """
        Check if the invoice is fully paid and update its status.
        """
        total_paid = Payment.objects.filter(
            invoice=invoice,
            status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if total_paid >= invoice.amount:
            invoice.status = Invoice.Status.PAID
            invoice.save(update_fields=['status'])
    
    @extend_schema(
        description="Confirm a pending payment",
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def confirm(self, request, pk=None):
        """
        Confirm a pending payment (admin only).
        """
        payment = self.get_object()
        
        if payment.status != 'pending':
            return Response(
                {"error": _("Payment is not in pending status")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        payment.status = 'success'
        payment.save(update_fields=['status'])
        
        # Update invoice status
        self._update_invoice_status(payment.invoice)
        
        return Response({"message": _("Payment confirmed successfully")})

class RefundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows refunds to be viewed or edited.
    """
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment__invoice']
    search_fields = ['payment__invoice__user__email', 'reason']
    ordering_fields = ['created_at', 'processed_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter refunds based on user role.
        Staff can see all refunds, regular users can only see refunds for their payments.
        """
        user = self.request.user
        if user.is_staff:
            return Refund.objects.all()
        return Refund.objects.filter(payment__invoice__user=user)
    
    @extend_schema(
        description="Approve a refund",
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """
        Approve a refund request (admin only).
        """
        refund = self.get_object()
        
        if refund.status != 'pending':
            return Response(
                {"error": _("Refund is not in pending status")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        refund.status = 'approved'
        refund.save(update_fields=['status'])
        
        return Response({"message": _("Refund approved successfully")})
    
    @extend_schema(
        description="Process a refund",
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def process(self, request, pk=None):
        """
        Process an approved refund (admin only).
        """
        refund = self.get_object()
        
        if refund.status != 'approved':
            return Response(
                {"error": _("Refund must be approved before processing")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        refund.status = 'completed'
        refund.processed_at = timezone.now()
        refund.save(update_fields=['status', 'processed_at'])
        
        # Check if the payment has been fully refunded
        total_refunded = Refund.objects.filter(
            payment=refund.payment,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # If the payment has been fully refunded, update the invoice status
        if total_refunded >= refund.payment.amount:
            invoice = refund.payment.invoice
            if invoice.status == Invoice.Status.PAID:
                invoice.status = Invoice.Status.PENDING
                invoice.save(update_fields=['status'])
        
        return Response({"message": _("Refund processed successfully")}) 