from django.contrib import admin
from .models import ProtectedContent, DetectionJob, ContentMatch, AIModel, ModelPerformanceLog, FeedbackData
for m in (ProtectedContent, DetectionJob, ContentMatch, AIModel, ModelPerformanceLog, FeedbackData): admin.site.register(m)
