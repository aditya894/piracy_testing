from rest_framework import serializers
from .models import Platform, ScanJob, ScanSchedule, ScannedContent, PlatformCredential

class PlatformSerializer(serializers.ModelSerializer):
    class Meta: model=Platform; fields=['id','name','display_name','base_url','icon_url','is_active']

class PlatformCredentialSerializer(serializers.ModelSerializer):
    class Meta: model=PlatformCredential; fields='__all__'; extra_kwargs={'access_token':{'write_only':True},'refresh_token':{'write_only':True}}

class ScanJobSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.display_name', read_only=True)
    class Meta:
        model=ScanJob
        fields=['id','user','platform','platform_name','keywords','content_types','scan_frequency','status','started_at','completed_at','total_items_scanned','error_message','job_type','created_at']
        read_only_fields=['id','user','status','started_at','completed_at','total_items_scanned','error_message','job_type','created_at']

class ScanScheduleSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.display_name', read_only=True)
    class Meta: model=ScanSchedule; fields='__all__'

class ScannedContentSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.display_name', read_only=True)
    class Meta:
        model=ScannedContent
        fields=['id','scan_job','platform','platform_name','platform_content_id','content_url','content_type','title','description','author','author_url','published_at','view_count','like_count','share_count','text_content','media_urls','metadata','content_hash','created_at']
        read_only_fields=['id','scan_job','platform','platform_name','created_at']
