from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Ticket, TicketComment, TicketAttachment
from apps.accounts.models import User
import tempfile
from PIL import Image
import io

class TicketModelTest(TestCase):
    """Tests for the Ticket model"""
    
    def setUp(self):
        # Create test users
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            role='customer'
        )
        
        self.technician = User.objects.create_user(
            username='technician',
            email='technician@example.com',
            password='password123',
            role='technician'
        )
        
        # Create test ticket
        self.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Test Ticket Description',
            created_by=self.customer,
            status=Ticket.Status.NEW,
            priority=Ticket.Priority.MEDIUM
        )
    
    def test_ticket_creation(self):
        """Test ticket creation"""
        self.assertEqual(self.ticket.title, 'Test Ticket')
        self.assertEqual(self.ticket.description, 'Test Ticket Description')
        self.assertEqual(self.ticket.created_by, self.customer)
        self.assertEqual(self.ticket.status, 'new')
        self.assertEqual(self.ticket.priority, 'medium')
        self.assertIsNone(self.ticket.assigned_to)
    
    def test_ticket_assignment(self):
        """Test ticket assignment"""
        self.ticket.assigned_to = self.technician
        self.ticket.status = Ticket.Status.ASSIGNED
        self.ticket.save()
        
        self.assertEqual(self.ticket.assigned_to, self.technician)
        self.assertEqual(self.ticket.status, 'assigned')
    
    def test_ticket_string_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.ticket), f"Ticket #{self.ticket.id} - Test Ticket")

class TicketCommentTest(TestCase):
    """Tests for the TicketComment model"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create test ticket
        self.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Test Ticket Description',
            created_by=self.user,
            status=Ticket.Status.NEW,
            priority=Ticket.Priority.MEDIUM
        )
        
        # Create test comment
        self.comment = TicketComment.objects.create(
            ticket=self.ticket,
            author=self.user,
            content='Test Comment',
            is_internal=False
        )
    
    def test_comment_creation(self):
        """Test comment creation"""
        self.assertEqual(self.comment.ticket, self.ticket)
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.content, 'Test Comment')
        self.assertFalse(self.comment.is_internal)

class TicketAPITest(TestCase):
    """Tests for the Ticket API"""
    
    def setUp(self):
        # Create test users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            role='admin',
            is_staff=True
        )
        
        self.technician = User.objects.create_user(
            username='technician',
            email='technician@example.com',
            password='password123',
            role='technician'
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            role='customer'
        )
        
        # Create test tickets
        self.ticket1 = Ticket.objects.create(
            title='Customer Ticket',
            description='Customer Ticket Description',
            created_by=self.customer,
            status=Ticket.Status.NEW,
            priority=Ticket.Priority.MEDIUM
        )
        
        self.ticket2 = Ticket.objects.create(
            title='Assigned Ticket',
            description='Assigned Ticket Description',
            created_by=self.customer,
            assigned_to=self.technician,
            status=Ticket.Status.ASSIGNED,
            priority=Ticket.Priority.HIGH
        )
        
        # Create API client
        self.client = APIClient()
    
    def test_ticket_list_customer(self):
        """Test that customers can only see their own tickets"""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(reverse('tickets:ticket-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Both tickets created by customer
    
    def test_ticket_list_technician(self):
        """Test that technicians can see assigned and unassigned tickets"""
        self.client.force_authenticate(user=self.technician)
        response = self.client.get(reverse('tickets:ticket-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Technician should see ticket2 (assigned to them) and ticket1 (unassigned)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_ticket_list_admin(self):
        """Test that admins can see all tickets"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('tickets:ticket-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # All tickets
    
    def test_ticket_create(self):
        """Test ticket creation"""
        self.client.force_authenticate(user=self.customer)
        data = {
            'title': 'New Ticket',
            'description': 'New Ticket Description',
            'priority': 'high'
        }
        response = self.client.post(reverse('tickets:ticket-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ticket.objects.count(), 3)
        self.assertEqual(Ticket.objects.get(title='New Ticket').created_by, self.customer)
    
    def test_ticket_assign(self):
        """Test ticket assignment"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'technician_id': self.technician.id
        }
        response = self.client.post(
            reverse('tickets:ticket-assign', args=[self.ticket1.id]), 
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket1.refresh_from_db()
        self.assertEqual(self.ticket1.assigned_to, self.technician)
        self.assertEqual(self.ticket1.status, 'assigned')
    
    def test_ticket_change_status(self):
        """Test ticket status change"""
        self.client.force_authenticate(user=self.technician)
        data = {
            'status': 'in_progress'
        }
        response = self.client.post(
            reverse('tickets:ticket-change-status', args=[self.ticket2.id]), 
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket2.refresh_from_db()
        self.assertEqual(self.ticket2.status, 'in_progress')
    
    def test_comment_create(self):
        """Test comment creation"""
        self.client.force_authenticate(user=self.customer)
        data = {
            'ticket': self.ticket1.id,
            'content': 'Test Comment'
        }
        response = self.client.post(reverse('tickets:comment-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TicketComment.objects.count(), 1)
        comment = TicketComment.objects.first()
        self.assertEqual(comment.author, self.customer)
        self.assertEqual(comment.ticket, self.ticket1)
        self.assertEqual(comment.content, 'Test Comment')
        self.assertFalse(comment.is_internal)
