from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Invoice, Payment, Refund
from apps.accounts.models import User
from apps.services.models import Service
from rest_framework.test import APIClient
from rest_framework import status

class InvoiceModelTest(TestCase):
    """Tests for the Invoice model"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Service Description',
            price=100.00
        )
        
        # Create test invoice
        self.invoice = Invoice.objects.create(
            user=self.user,
            service=self.service,
            amount=Decimal('100.00'),
            status=Invoice.Status.PENDING,
            due_date=timezone.now().date() + timedelta(days=30)
        )
    
    def test_invoice_creation(self):
        """Test invoice creation"""
        self.assertEqual(self.invoice.user, self.user)
        self.assertEqual(self.invoice.service, self.service)
        self.assertEqual(self.invoice.amount, Decimal('100.00'))
        self.assertEqual(self.invoice.status, 'pending')
    
    def test_string_representation(self):
        """Test string representation of invoice"""
        self.assertEqual(
            str(self.invoice),
            f"Invoice #{self.invoice.id} - {self.user.email}"
        )

class PaymentModelTest(TestCase):
    """Tests for the Payment model"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Service Description',
            price=100.00
        )
        
        # Create test invoice
        self.invoice = Invoice.objects.create(
            user=self.user,
            service=self.service,
            amount=Decimal('100.00'),
            status=Invoice.Status.PENDING,
            due_date=timezone.now().date() + timedelta(days=30)
        )
        
        # Create test payment
        self.payment = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal('100.00'),
            method=Payment.Method.CREDIT_CARD,
            transaction_id='test-transaction-123',
            status='success'
        )
    
    def test_payment_creation(self):
        """Test payment creation"""
        self.assertEqual(self.payment.invoice, self.invoice)
        self.assertEqual(self.payment.amount, Decimal('100.00'))
        self.assertEqual(self.payment.method, 'credit_card')
        self.assertEqual(self.payment.status, 'success')
    
    def test_invoice_status_update(self):
        """Test that invoice status is updated when payment is successful"""
        # Refresh invoice from database
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'paid')

class InvoiceAPITest(TestCase):
    """Tests for the Invoice API"""
    
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='user123'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Service Description',
            price=100.00
        )
        
        # Create test invoice
        self.invoice = Invoice.objects.create(
            user=self.regular_user,
            service=self.service,
            amount=Decimal('100.00'),
            status=Invoice.Status.PENDING,
            due_date=timezone.now().date() + timedelta(days=30)
        )
        
        # Create API client
        self.client = APIClient()
    
    def test_invoice_list_admin(self):
        """Test that admin can see all invoices"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('payments:invoice-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_invoice_list_user(self):
        """Test that user can only see their own invoices"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(reverse('payments:invoice-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Create another user with an invoice
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='other123'
        )
        
        Invoice.objects.create(
            user=other_user,
            service=self.service,
            amount=Decimal('100.00'),
            status=Invoice.Status.PENDING,
            due_date=timezone.now().date() + timedelta(days=30)
        )
        
        # Regular user should still only see their own invoice
        response = self.client.get(reverse('payments:invoice-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1) 