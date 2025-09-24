from rest_framework import serializers
from .models import ProtectedContent, DetectionJob, ContentMatch, AIModel, ModelPerformanceLog, FeedbackData
class ProtectedContentSerializer(serializers.ModelSerializer):
    class Meta: model=ProtectedContent; fields='__all__'
class DetectionJobSerializer(serializers.ModelSerializer):
    class Meta: model=DetectionJob; fields='__all__'
class ContentMatchSerializer(serializers.ModelSerializer):
    class Meta: model=ContentMatch; fields='__all__'
class AIModelSerializer(serializers.ModelSerializer):
    class Meta: model=AIModel; fields='__all__'
class ModelPerformanceLogSerializer(serializers.ModelSerializer):
    class Meta: model=ModelPerformanceLog; fields='__all__'
class FeedbackDataSerializer(serializers.ModelSerializer):
    class Meta: model=FeedbackData; fields='__all__'
