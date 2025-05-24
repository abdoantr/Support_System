from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import FAQ
from apps.tickets.models import Ticket, TicketAttachment
from apps.services.models import Service
from apps.kb.models import KnowledgeBaseArticle, ArticleCategory, Tag
from django.utils import timezone
import random
import json

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

        # Get or create test users with specified emails
        try:
            customer = User.objects.get(email='antr@customer.com')
            self.stdout.write(self.style.SUCCESS(f'Found customer user: antr@customer.com'))
            
            # Clear existing tickets for this user
            Ticket.objects.filter(created_by=customer).delete()
            self.stdout.write("Cleared existing tickets for user")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User antr@customer.com not found'))
            return

        try:
            technician = User.objects.get(email='antr@technician.com')
            self.stdout.write(self.style.SUCCESS(f'Found technician user: antr@technician.com'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User antr@technician.com not found'))
            return

        # Get available services from database
        services = list(Service.objects.filter(is_active=True))
        if not services:
            self.stdout.write(self.style.ERROR('No active services found in database'))
            return

        # Create tickets with different statuses
        statuses = ['new', 'assigned', 'in_progress', 'pending', 'resolved', 'closed']
        
        for ticket_data in ticket_samples:
            status = random.choice(statuses)
            service = random.choice(services)  # Randomly select from existing services
            
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

        # Create Knowledge Base Articles
        try:
            # Create categories
            categories_data = [
                {'name': 'Hardware', 'description': 'Hardware-related articles and guides'},
                {'name': 'Software', 'description': 'Software installation and troubleshooting'},
                {'name': 'Network', 'description': 'Network configuration and issues'},
                {'name': 'Security', 'description': 'Security best practices and guides'},
                {'name': 'Common Issues', 'description': 'Frequently encountered problems and solutions'}
            ]

            categories = []
            for cat_data in categories_data:
                category, created = ArticleCategory.objects.get_or_create(
                    name=cat_data['name'],
                    defaults={'description': cat_data['description']}
                )
                categories.append(category)

            # Create tags
            tags_data = ['Windows', 'Linux', 'Hardware', 'Software', 'Network', 'Security',
                        'Troubleshooting', 'Guide', 'Tutorial', 'Best Practices']
            
            tags = []
            for tag_name in tags_data:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                tags.append(tag)

            # Sample article data
            articles_data = [
                {
                    'title': 'Common Printer Issues and Solutions',
                    'short_description': 'A comprehensive guide to resolving common printer problems',
                    'content': '''
# Common Printer Issues and Solutions

## Connection Issues
- Check physical connections
- Verify network connectivity
- Restart printer and computer

## Paper Jams
1. Open printer doors carefully
2. Remove jammed paper gently
3. Check for torn pieces
4. Close doors properly

## Driver Problems
- Update printer drivers
- Reinstall if necessary
- Check manufacturer website
                    ''',
                    'category': 'Hardware',
                    'tags': ['Hardware', 'Troubleshooting', 'Guide'],
                    'is_featured': True
                },
                {
                    'title': 'Network Security Best Practices',
                    'short_description': 'Essential security practices for maintaining a secure network',
                    'content': '''
# Network Security Best Practices

## Password Policies
- Use strong passwords
- Regular password changes
- Two-factor authentication

## Firewall Configuration
1. Enable firewall
2. Configure rules properly
3. Regular monitoring
4. Log analysis

## Access Control
- Implement least privilege
- Regular access reviews
- Monitor suspicious activity
                    ''',
                    'category': 'Security',
                    'tags': ['Security', 'Network', 'Best Practices'],
                    'is_featured': True
                },
                {
                    'title': 'Software Installation Guide',
                    'short_description': 'Step-by-step guide for software installation',
                    'content': '''
# Software Installation Guide

## Pre-installation Steps
1. Check system requirements
2. Backup important data
3. Close other applications

## Installation Process
- Download from official source
- Verify checksums
- Run as administrator
- Follow wizard steps

## Post-installation
- Update to latest version
- Configure settings
- Test functionality
                    ''',
                    'category': 'Software',
                    'tags': ['Software', 'Guide', 'Tutorial'],
                    'is_featured': False
                }
            ]

            # Create articles
            for article_data in articles_data:
                # Get category
                category = ArticleCategory.objects.get(name=article_data['category'])
                
                # Create article
                article = KnowledgeBaseArticle.objects.create(
                    title=article_data['title'],
                    short_description=article_data['short_description'],
                    content=article_data['content'],
                    category=category,
                    created_by=technician,
                    updated_by=technician,
                    is_featured=article_data['is_featured'],
                    visibility='public',
                    status='published'
                )
    
                # Handle tags separately
                article.tags = json.dumps(article_data['tags'])
                article.save()

            self.stdout.write(self.style.SUCCESS('Successfully created knowledge base articles'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating knowledge base articles: {str(e)}'))
