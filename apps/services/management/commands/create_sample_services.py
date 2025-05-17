from django.core.management.base import BaseCommand
from apps.services.models import Service, ServiceFeature

class Command(BaseCommand):
    help = 'Creates sample services and features for demonstration'

    def handle(self, *args, **kwargs):
        # Create service features
        features = {
            'hardware': [
                'On-site support',
                'Hardware diagnostics',
                'Parts replacement',
                'Performance optimization',
                'Preventive maintenance',
            ],
            'software': [
                '24/7 remote support',
                'Software installation',
                'System updates',
                'Data backup',
                'Security patches',
            ],
            'network': [
                'Network monitoring',
                'Firewall configuration',
                'VPN setup',
                'Bandwidth optimization',
                'Security assessment',
            ],
            'security': [
                'Vulnerability scanning',
                'Malware removal',
                'Security audits',
                'Access control',
                'Incident response',
            ]
        }

        # Create features
        created_features = {}
        for category, feature_list in features.items():
            category_features = []
            for feature_name in feature_list:
                feature, created = ServiceFeature.objects.get_or_create(
                    name=feature_name,
                    defaults={'description': f'Detailed description for {feature_name}'}
                )
                category_features.append(feature)
            created_features[category] = category_features

        # Create services
        services_data = [
            {
                'name': 'Hardware Repair & Maintenance',
                'description': 'Professional hardware repair and maintenance services for all your devices. Our expert technicians provide quick and reliable solutions for any hardware issues.',
                'category': 'hardware',
                'price': 99.99,
                'price_period': 'per service',
                'is_featured': True,
            },
            {
                'name': 'Software Installation & Support',
                'description': 'Comprehensive software support including installation, configuration, and troubleshooting. Get your software running smoothly with our expert assistance.',
                'category': 'software',
                'price': 49.99,
                'price_period': 'monthly',
                'is_featured': True,
            },
            {
                'name': 'Network Setup & Security',
                'description': 'Professional network installation and security services. We ensure your network is fast, secure, and reliable.',
                'category': 'network',
                'price': 149.99,
                'price_period': 'monthly',
                'is_featured': True,
            },
            {
                'name': 'Cybersecurity Solutions',
                'description': 'Comprehensive cybersecurity services to protect your digital assets. We provide advanced security measures against modern threats.',
                'category': 'security',
                'price': 199.99,
                'price_period': 'monthly',
                'is_featured': True,
            },
            {
                'name': 'Data Recovery Services',
                'description': 'Professional data recovery services for all storage devices. We help you recover your valuable data quickly and securely.',
                'category': 'hardware',
                'price': 299.99,
                'price_period': 'per service',
                'is_featured': False,
            },
            {
                'name': 'Cloud Solutions',
                'description': 'Complete cloud services including setup, migration, and management. Transform your business with our cloud expertise.',
                'category': 'software',
                'price': 79.99,
                'price_period': 'monthly',
                'is_featured': False,
            },
            {
                'name': 'Wireless Network Solutions',
                'description': 'Professional wireless network design and implementation. Optimize your wireless coverage and performance.',
                'category': 'network',
                'price': 129.99,
                'price_period': 'per service',
                'is_featured': False,
            },
            {
                'name': 'Security Audit & Compliance',
                'description': 'Comprehensive security audits and compliance assessments. Ensure your systems meet industry standards.',
                'category': 'security',
                'price': 399.99,
                'price_period': 'per audit',
                'is_featured': False,
            },
        ]

        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'category': service_data['category'],
                    'price': service_data['price'],
                    'price_period': service_data['price_period'],
                    'is_featured': service_data['is_featured'],
                }
            )
            
            # Add features
            service.features.set(created_features[service_data['category']])
            
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{status} service: {service.name}'))
