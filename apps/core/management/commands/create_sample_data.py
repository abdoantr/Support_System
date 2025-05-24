from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import FAQ
from apps.tickets.models import Ticket, TicketAttachment
from apps.services.models import Service
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample FAQ entries and support tickets'

    def handle(self, *args, **options):
        # Sample FAQ data
        faq_data = [
            {
                'category': 'technical',
                'question': 'How do I reset my password?',
                'answer': 'You can reset your password by clicking on the "Forgot Password" link on the login page. Follow the instructions sent to your email to create a new password.',
                'order': 1
            },
            {
                'category': 'technical',
                'question': 'How can I update my profile information?',
                'answer': 'Log in to your account, click on your profile picture or name, and select "Profile" from the dropdown menu. Click "Edit Profile" to update your information.',
                'order': 2
            },
            {
                'category': 'billing',
                'question': 'What payment methods do you accept?',
                'answer': 'We accept major credit cards (Visa, MasterCard, American Express), PayPal, and bank transfers for business accounts.',
                'order': 1
            },
            {
                'category': 'billing',
                'question': 'How do I view my billing history?',
                'answer': "You can view your billing history by going to Settings > Billing > Payment History. Here you'll find all your past transactions and invoices.",
                'order': 2
            },
            {
                'category': 'services',
                'question': 'What support services do you offer?',
                'answer': 'We offer technical support, software troubleshooting, hardware maintenance, network configuration, security assessments, and IT consulting services.',
                'order': 1
            },
            {
                'category': 'services',
                'question': 'What are your support hours?',
                'answer': 'Our standard support hours are Monday to Friday, 9 AM to 6 PM. Premium support plans include 24/7 emergency assistance.',
                'order': 2
            },
            {
                'category': 'technical',
                'question': 'How do I submit a support ticket?',
                'answer': 'Click on "Support" in the main menu, then select "Create Ticket". Fill out the ticket form with your issue details and submit.',
                'order': 3
            },
            {
                'category': 'billing',
                'question': 'How do refunds work?',
                'answer': 'Refund requests are processed within 3-5 business days. Contact our billing department through a support ticket for refund inquiries.',
                'order': 3
            }
        ]

        # Create FAQ entries
        for faq in faq_data:
            FAQ.objects.get_or_create(
                question=faq['question'],
                defaults={
                    'category': faq['category'],
                    'answer': faq['answer'],
                    'order': faq['order']
                }
            )
        self.stdout.write(self.style.SUCCESS('Successfully created FAQ entries'))

        # Create or get default service
        service, created = Service.objects.get_or_create(
            name='Technical Support',
            defaults={
                'description': 'General technical support and troubleshooting',
                'is_active': True
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Using service: {service.name} (ID: {service.id})'))

        # Sample ticket subjects and descriptions
        ticket_samples = [
            {
                'title': 'Unable to access email',
                'description': 'Getting "Connection refused" error when trying to access company email since this morning.',
                'priority': 'high',
                'category': 'Email Issues'
            },
            {
                'title': 'Printer not working',
                'description': 'The office printer on 2nd floor is showing offline status and won\'t print any documents.',
                'priority': 'medium',
                'category': 'Hardware'
            },
            {
                'title': 'Software license expired',
                'description': 'Need to renew the team\'s design software licenses which expired yesterday.',
                'priority': 'medium',
                'category': 'Software'
            },
            {
                'title': 'Server down',
                'description': 'Production server is not responding. All services are affected.',
                'priority': 'urgent',
                'category': 'Infrastructure'
            },
            {
                'title': 'Need software installation',
                'description': 'Please install the latest version of Python and required development tools on my workstation.',
                'priority': 'low',
                'category': 'Software'
            },
            {
                'title': 'Password reset required',
                'description': 'Locked out of my account after multiple failed login attempts.',
                'priority': 'high',
                'category': 'Account Access'
            },
            {
                'title': 'Network connectivity issues',
                'description': 'Experiencing slow internet connection and frequent disconnections in the marketing department.',
                'priority': 'high',
                'category': 'Network'
            },
            {
                'title': 'Data backup failure',
                'description': 'Last night\'s automated backup failed. Need immediate assistance to ensure data safety.',
                'priority': 'urgent',
                'category': 'Data Management'
            },
            {
                'title': 'Mobile app crashing',
                'description': 'Company mobile app keeps crashing when users try to access the reports section.',
                'priority': 'high',
                'category': 'Mobile Apps'
            },
            {
                'title': 'Security alert investigation',
                'description': 'Received multiple security alerts from the firewall. Need investigation and resolution.',
                'priority': 'urgent',
                'category': 'Security'
            }
        ]

        from django.core.files.base import ContentFile
        import os

        # Sample text for attachments
        attachment_samples = {
            'error_log.txt': 'Error occurred at timestamp: 2025-05-24 09:30:00\nStack trace follows:\n...',
            'network_report.txt': 'Network Analysis Report\nDowntime detected: 15 minutes\nAffected services: ...',
            'screenshot.txt': 'Error message screenshot content simulation',
            'system_info.txt': 'OS: Windows 11\nRAM: 16GB\nCPU: Intel i7\nStorage: 500GB SSD'
        }

        # Get or create a sample user for tickets
        import uuid

        # Get or create test users with unique usernames
        def get_unique_username(base_name):
            username = f"{base_name}_{str(uuid.uuid4())[:8]}"
            return username

        # Get the specific user
        try:
            customer = User.objects.get(email='antr@customer.com')
            self.stdout.write(self.style.SUCCESS(f'Found user: antr@customer.com'))
            
            # Clear existing tickets for this user
            Ticket.objects.filter(created_by=customer).delete()
            self.stdout.write("Cleared existing tickets for user")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User antr@customer.com not found'))
            return

        try:
            technician = User.objects.get(email='technician@example.com')
        except User.DoesNotExist:
            technician = User.objects.create_user(
                username=get_unique_username('technician'),
                email='technician@example.com',
                password='securepassword123',
                first_name='Sample',
                last_name='Technician',
                is_active=True,
                role='TECHNICIAN'
            )

        # Create tickets with different statuses
        statuses = ['new', 'assigned', 'in_progress', 'pending', 'resolved', 'closed']
        
        for ticket_data in ticket_samples:
            status = random.choice(statuses)
            # Use the single service for all tickets
            
            ticket = Ticket.objects.create(
                title=ticket_data['title'],
                description=ticket_data['description'],
                created_by=customer,
                status=status,
                priority=ticket_data['priority'],
                service=service
            )
            
            if status in ['assigned', 'in_progress', 'resolved', 'closed']:
                ticket.assigned_to = technician
                ticket.save()

            # Add due date for some tickets
            if random.choice([True, False]):
                days_offset = random.randint(-5, 10)
                ticket.due_date = timezone.now() + timezone.timedelta(days=days_offset)
                ticket.save()

            # Add attachments to some tickets
            if random.choice([True, False]):
                # Randomly select 1-3 attachments
                selected_attachments = random.sample(list(attachment_samples.items()),
                                                  random.randint(1, min(3, len(attachment_samples))))
                for filename, content in selected_attachments:
                    attachment = TicketAttachment.objects.create(
                        ticket=ticket,
                        uploaded_by=customer if random.choice([True, False]) else technician,
                        description=f'Sample {filename}',
                    )
                    # Create and save the file
                    attachment.file.save(
                        filename,
                        ContentFile(content.encode('utf-8')),
                        save=True
                    )

        self.stdout.write(self.style.SUCCESS('Successfully created sample tickets'))