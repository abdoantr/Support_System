from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from .models import Service, ServiceFeature
from apps.accounts.models import User

class ServiceModelTest(TestCase):
    """Tests for the Service model"""
    
    def setUp(self):
        # Create test feature
        self.feature = ServiceFeature.objects.create(
            name='Test Feature',
            description='Test Feature Description'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Service Description',
            category='software',
            price=Decimal('100.00'),
            price_period='month',
            is_featured=True,
            is_active=True
        )
        self.service.features.add(self.feature)
    
    def test_service_creation(self):
        """Test service creation"""
        self.assertEqual(self.service.name, 'Test Service')
        self.assertEqual(self.service.description, 'Test Service Description')
        self.assertEqual(self.service.category, 'software')
        self.assertEqual(self.service.price, Decimal('100.00'))
        self.assertEqual(self.service.price_period, 'month')
        self.assertTrue(self.service.is_featured)
        self.assertTrue(self.service.is_active)
        self.assertEqual(self.service.features.count(), 1)
    
    def test_string_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.service), 'Test Service')
        self.assertEqual(str(self.feature), 'Test Feature')

class ServiceAPITest(TestCase):
    """Tests for the Service API"""
    
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password123'
        )
        
        # Create test feature
        self.feature = ServiceFeature.objects.create(
            name='Test Feature',
            description='Test Feature Description'
        )
        
        # Create test services
        self.service1 = Service.objects.create(
            name='Active Service',
            description='Active Service Description',
            category='software',
            price=Decimal('100.00'),
            price_period='month',
            is_featured=True,
            is_active=True
        )
        self.service1.features.add(self.feature)
        
        self.service2 = Service.objects.create(
            name='Inactive Service',
            description='Inactive Service Description',
            category='hardware',
            price=Decimal('200.00'),
            price_period='year',
            is_featured=False,
            is_active=False
        )
        
        self.client = APIClient()
    
    def test_list_services_unauthenticated(self):
        """Test that unauthenticated users can't see services"""
        response = self.client.get(reverse('services:service-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_services_regular_user(self):
        """Test that regular users can only see active services"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(reverse('services:service-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only active service
    
    def test_list_services_admin(self):
        """Test that admin users can see all services"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('services:service-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # All services
    
    def test_create_service_regular_user(self):
        """Test that regular users cannot create services"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'name': 'New Service',
            'description': 'New Service Description',
            'category': 'software',
            'price': '150.00',
            'is_active': True
        }
        response = self.client.post(reverse('services:service-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_service_admin(self):
        """Test that admin users can create services"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'New Service',
            'description': 'New Service Description',
            'category': 'software',
            'price': '150.00',
            'is_active': True
        }
        response = self.client.post(reverse('services:service-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 3)
    
    def test_featured_services(self):
        """Test featured services endpoint"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(reverse('services:service-featured'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Active Service')
    
    def test_by_category(self):
        """Test by_category endpoint"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{reverse('services:service-by-category')}?category=software")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Active Service')
