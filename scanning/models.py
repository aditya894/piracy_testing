from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Platform(models.Model):
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    base_url = models.URLField()
    api_endpoint = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    icon_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table='platforms'; ordering=['display_name']
    def __str__(self): return self.display_name

class ScanJob(models.Model):
    STATUS = [('pending','Pending'),('running','Running'),('completed','Completed'),('failed','Failed'),('cancelled','Cancelled')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scan_jobs')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='scan_jobs')
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    job_type = models.CharField(max_length=20, choices=[('manual','Manual'),('scheduled','Scheduled'),('triggered','Triggered')], default='manual')
    keywords = models.JSONField(default=list)
    content_types = models.JSONField(default=list)
    scan_frequency = models.CharField(max_length=20, choices=[('daily','Daily'),('weekly','Weekly'),('monthly','Monthly')], default='daily')
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    total_items_scanned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table='scan_jobs'; ordering=['-created_at']
    def __str__(self): return f"Scan Job {self.id} - {self.platform.display_name} ({self.status})"

class ScannedContent(models.Model):
    CONTENT_TYPES = [('text','Text'),('image','Image'),('video','Video'),('audio','Audio'),('document','Document')]
    scan_job = models.ForeignKey(ScanJob, on_delete=models.CASCADE, related_name='scanned_content')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    platform_content_id = models.CharField(max_length=255)
    content_url = models.URLField()
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    title = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    author_url = models.URLField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    view_count = models.IntegerField(blank=True, null=True)
    like_count = models.IntegerField(blank=True, null=True)
    share_count = models.IntegerField(blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    media_urls = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    content_hash = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table='scanned_content'
        indexes=[models.Index(fields=['content_hash']), models.Index(fields=['published_at'])]
    def __str__(self): return f"{self.platform.display_name} - {self.title or self.platform_content_id}"

class ScanSchedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scan_schedules')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='scan_schedules')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    frequency = models.CharField(max_length=20, choices=[('daily','Daily'),('weekly','Weekly'),('monthly','Monthly')])
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(blank=True, null=True)
    next_run_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table='scan_schedules'; ordering=['-created_at']

class PlatformCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='platform_credentials')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='credentials')
    access_token = models.CharField(max_length=500, blank=True, null=True)
    refresh_token = models.CharField(max_length=500, blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table='platform_credentials'; unique_together=[('user','platform')]
    def __str__(self): return f"{self.user.email} - {self.platform.display_name}"
    def is_token_expired(self):
        from django.utils import timezone
        return bool(self.token_expires_at and timezone.now()>self.token_expires_at)
