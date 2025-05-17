from django.db import models
from django.utils.translation import gettext_lazy as _

class ServiceFeature(models.Model):
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    
    def __str__(self):
        return self.name

class Service(models.Model):
    CATEGORIES = [
        ('hardware', _('Hardware')),
        ('software', _('Software')),
        ('network', _('Network')),
        ('security', _('Security')),
    ]
    
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'))
    category = models.CharField(_('category'), max_length=20, choices=CATEGORIES, default='software')
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, default=0)
    price_period = models.CharField(_('price period'), max_length=20, blank=True)
    image = models.ImageField(_('image'), upload_to='services/', null=True, blank=True)
    features = models.ManyToManyField(ServiceFeature, related_name='services', blank=True)
    is_featured = models.BooleanField(_('is featured'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')
        ordering = ['name']
    
    def __str__(self):
        return self.name
