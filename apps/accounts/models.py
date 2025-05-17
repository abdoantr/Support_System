from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        TECHNICIAN = 'technician', _('Technician')
        CUSTOMER = 'customer', _('Customer')

    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # الحقول الإضافية للفنيين
    specialization = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)
    
    # Email verification fields
    email_verified = models.BooleanField(_('email verified'), default=False)
    email_verification_token = models.CharField(max_length=255, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # تعديل الحقول المطلوبة
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_initials(self):
        """
        Get user's initials from first name and last name
        """
        initials = ""
        if self.first_name:
            initials += self.first_name[0].upper()
        if self.last_name:
            initials += self.last_name[0].upper()
        
        # If no initials could be derived, use first letter of email or username
        if not initials:
            if self.email:
                initials = self.email[0].upper()
            else:
                initials = self.username[0].upper()
        
        return initials

    def send_verification_email(self, request=None):
        """Send email verification link to the user."""
        token = default_token_generator.make_token(self)
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        
        context = {
            'user': self,
            'domain': request.get_host() if request else settings.SITE_URL,
            'protocol': 'https' if request and request.is_secure() else 'http',
            'uid': uid,
            'token': token,
            'site_name': settings.SITE_NAME,
        }
        
        subject = render_to_string('users/email/email_verification_subject.txt', context)
        message = render_to_string('users/email/email_verification_email.html', context)
        
        self.email_verification_token = token
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        
        send_mail(
            subject.strip(),
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            html_message=message,
        )