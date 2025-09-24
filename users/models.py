from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    subscription_plan = models.CharField(max_length=20, choices=[('basic','Basic'),('pro','Pro'),('enterprise','Enterprise')], default='basic')
    is_verified = models.BooleanField(default=False)
    class Meta: db_table='users'
    def __str__(self): return self.email or self.username

class UserProfile(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    notification_preferences = models.JSONField(default=dict)
    api_key = models.CharField(max_length=255, unique=True, blank=True, null=True)
    api_key_created_at = models.DateTimeField(blank=True, null=True)
    class Meta: db_table='user_profiles'
    def __str__(self): return f"Profile for {self.user.email}"

class ClientConfiguration(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='configuration')
    scan_youtube = models.BooleanField(default=True)
    scan_facebook = models.BooleanField(default=True)
    scan_instagram = models.BooleanField(default=True)
    scan_telegram = models.BooleanField(default=False)
    scan_whatsapp = models.BooleanField(default=False)
    monitor_text = models.BooleanField(default=True)
    monitor_images = models.BooleanField(default=True)
    monitor_videos = models.BooleanField(default=True)
    keywords = models.JSONField(default=list)
    content_domains = models.JSONField(default=list)
    similarity_threshold = models.FloatField(default=0.8)
    email_alerts = models.BooleanField(default=True)
    sms_alerts = models.BooleanField(default=False)
    in_app_notifications = models.BooleanField(default=True)
    auto_report_enabled = models.BooleanField(default=False)
    require_manual_approval = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table='client_configurations'

class ActivityLog(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta: db_table='activity_logs'; ordering=['-timestamp']
    def __str__(self): return f"{self.user.email} - {self.action} at {self.timestamp}"
