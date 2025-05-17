from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Checks if the current settings are suitable for production deployment'

    def handle(self, *args, **options):
        checks = []
        warnings = []
        
        # Check DEBUG setting
        if settings.DEBUG:
            checks.append(('DEBUG', 'ERROR', 'DEBUG is set to True. This should be False in production.'))
        else:
            checks.append(('DEBUG', 'OK', 'DEBUG is properly set to False.'))
        
        # Check SECRET_KEY
        if settings.SECRET_KEY == 'django-insecure-+p*sr%v-6pw2!6z2egpnv2n5zc_y3=w3-y2)ed#-y3q0@cgk&e':
            checks.append(('SECRET_KEY', 'ERROR', 'You are using the default SECRET_KEY. Generate a new one for production.'))
        elif 'django-insecure' in settings.SECRET_KEY:
            checks.append(('SECRET_KEY', 'ERROR', 'Your SECRET_KEY contains "django-insecure". Generate a new one for production.'))
        elif len(settings.SECRET_KEY) < 50:
            checks.append(('SECRET_KEY', 'WARNING', 'Your SECRET_KEY is possibly too short. Consider generating a stronger one.'))
        else:
            checks.append(('SECRET_KEY', 'OK', 'SECRET_KEY appears to be properly configured.'))
        
        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            checks.append(('ALLOWED_HOSTS', 'ERROR', 'ALLOWED_HOSTS is not configured properly. Use specific host names in production.'))
        elif set(settings.ALLOWED_HOSTS) == {'localhost', '127.0.0.1'}:
            checks.append(('ALLOWED_HOSTS', 'WARNING', 'ALLOWED_HOSTS only contains development hosts. Add your production domain.'))
        else:
            checks.append(('ALLOWED_HOSTS', 'OK', 'ALLOWED_HOSTS is configured.'))
        
        # Check database
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            checks.append(('DATABASE', 'WARNING', 'You are using SQLite. Consider using a more robust database for production.'))
        else:
            checks.append(('DATABASE', 'OK', 'Using a production-suitable database.'))
            
        # Check email settings
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            checks.append(('EMAIL', 'ERROR', 'Using console email backend. Use SMTP backend for production.'))
        elif not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            checks.append(('EMAIL', 'ERROR', 'Missing email credentials. Configure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD.'))
        else:
            checks.append(('EMAIL', 'OK', 'Email settings appear to be configured.'))
        
        # Check security settings
        if not hasattr(settings, 'SECURE_SSL_REDIRECT') or not settings.SECURE_SSL_REDIRECT:
            warnings.append('Consider enabling SECURE_SSL_REDIRECT for HTTPS')
        
        if not hasattr(settings, 'SECURE_HSTS_SECONDS') or settings.SECURE_HSTS_SECONDS < 31536000:
            warnings.append('Consider enabling or increasing SECURE_HSTS_SECONDS (recommended: 31536000)')
        
        if not hasattr(settings, 'CSRF_COOKIE_SECURE') or not settings.CSRF_COOKIE_SECURE:
            warnings.append('CSRF_COOKIE_SECURE should be enabled in production')
        
        if not hasattr(settings, 'SESSION_COOKIE_SECURE') or not settings.SESSION_COOKIE_SECURE:
            warnings.append('SESSION_COOKIE_SECURE should be enabled in production')
        
        # Display results
        self.stdout.write(self.style.SUCCESS('\n=== Production Settings Check ===\n'))
        
        for check_name, status, message in checks:
            if status == 'OK':
                self.stdout.write(f"{check_name}: {self.style.SUCCESS(status)} - {message}")
            elif status == 'WARNING':
                self.stdout.write(f"{check_name}: {self.style.WARNING(status)} - {message}")
            else:
                self.stdout.write(f"{check_name}: {self.style.ERROR(status)} - {message}")
        
        if warnings:
            self.stdout.write('\n' + self.style.WARNING('Additional security recommendations:'))
            for warning in warnings:
                self.stdout.write(f"- {warning}")
            
        # Summary
        errors = sum(1 for _, status, _ in checks if status == 'ERROR')
        warnings = sum(1 for _, status, _ in checks if status == 'WARNING') + len(warnings)
        
        self.stdout.write('\n' + self.style.SUCCESS(f'Summary: {errors} errors, {warnings} warnings'))
        
        if errors > 0:
            self.stdout.write(self.style.ERROR('✖ Your settings are NOT ready for production deployment'))
        elif warnings > 0:
            self.stdout.write(self.style.WARNING('⚠ Your settings may need improvements before deployment'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Your settings appear to be production-ready')) 