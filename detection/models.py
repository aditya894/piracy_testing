from django.db import models
from django.contrib.auth import get_user_model
from scanning.models import ScannedContent
User = get_user_model()

class ProtectedContent(models.Model):
    CONTENT_TYPE_CHOICES=[('text','Text'),('image','Image'),('video','Video')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='protected_content')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    text_content = models.TextField(blank=True, null=True)
    file_path = models.FileField(upload_to='protected_content/', blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)
    content_hash = models.CharField(max_length=64)
    text_fingerprint = models.JSONField(default=dict)
    visual_fingerprint = models.JSONField(default=dict)
    audio_fingerprint = models.JSONField(default=dict)
    tags = models.JSONField(default=list)
    category = models.CharField(max_length=100, blank=True, null=True)
    copyright_info = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    monitoring_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table='protected_content'

class DetectionJob(models.Model):
    STATUS=[('pending','Pending'),('processing','Processing'),('completed','Completed'),('failed','Failed')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detection_jobs')
    scanned_content = models.ForeignKey(ScannedContent, on_delete=models.CASCADE, related_name='detection_jobs')
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    detection_types = models.JSONField(default=list)
    similarity_threshold = models.FloatField(default=0.8)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    model_versions = models.JSONField(default=dict)
    processing_time = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table='detection_jobs'

class ContentMatch(models.Model):
    MATCH_TYPES=[('exact','Exact'),('partial','Partial')]
    detection_job = models.ForeignKey(DetectionJob, on_delete=models.CASCADE, related_name='matches')
    protected_content = models.ForeignKey(ProtectedContent, on_delete=models.CASCADE, related_name='matches')
    scanned_content = models.ForeignKey(ScannedContent, on_delete=models.CASCADE, related_name='matches')
    match_type = models.CharField(max_length=20, choices=MATCH_TYPES)
    confidence_level = models.CharField(max_length=20, choices=[('low','Low'),('medium','Medium'),('high','High')], default='low')
    similarity_score = models.FloatField(default=0.0)
    matched_segments = models.JSONField(default=list)
    match_metadata = models.JSONField(default=dict)
    is_reviewed = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(blank=True, null=True)
    reviewer_notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_matches')
    reviewed_at = models.DateTimeField(blank=True, null=True)
    action_taken = models.CharField(max_length=20, choices=[('none','No Action'),('reported','Reported'),('takedown','Takedown Requested'),('ignored','Ignored')], default='none')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table='content_matches'; unique_together=[('protected_content','scanned_content')]

class AIModel(models.Model):
    MODEL_TYPES=[('text','Text'),('image','Image'),('video','Video')]
    name=models.CharField(max_length=100)
    model_type=models.CharField(max_length=20, choices=MODEL_TYPES)
    version=models.CharField(max_length=50, default='1.0')
    description=models.TextField(blank=True, null=True)
    is_active=models.BooleanField(default=True)
    is_default=models.BooleanField(default=False)
    model_path=models.CharField(max_length=500, blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table='ai_models'

class ModelPerformanceLog(models.Model):
    model=models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='performance_logs')
    processing_time=models.FloatField(); accuracy=models.FloatField(); precision=models.FloatField(); recall=models.FloatField(); f1_score=models.FloatField()
    test_dataset_size=models.IntegerField(); test_date=models.DateTimeField(); test_notes=models.TextField(blank=True, null=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table='model_performance_logs'; ordering=['-test_date']

class FeedbackData(models.Model):
    FEEDBACK_TYPES=[('false_positive','False Positive'),('false_negative','False Negative'),('improvement','Improvement Suggestion')]
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback')
    content_match=models.ForeignKey(ContentMatch, on_delete=models.CASCADE, related_name='feedback', blank=True, null=True)
    feedback_type=models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    description=models.TextField(blank=True, null=True)
    metadata=models.JSONField(default=dict)
    is_processed=models.BooleanField(default=False)
    processed_at=models.DateTimeField(blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table='feedback_data'; ordering=['-created_at']
