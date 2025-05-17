from django.db import models
from django.conf import settings

class TechnicianProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='technician_profile')
    job_title = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True, null=True)
    skill_ratings = models.JSONField(default=dict, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username}'s Technician Profile" 