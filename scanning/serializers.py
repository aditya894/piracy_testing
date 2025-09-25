from rest_framework import serializers
from .models import Platform, ScanJob, ScanSchedule, ScannedContent, PlatformCredential
import hashlib, json

class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ['id', 'name', 'display_name', 'base_url', 'icon_url', 'is_active']

class PlatformCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformCredential
        fields = '__all__'
        extra_kwargs = {
            'access_token': {'write_only': True},
            'refresh_token': {'write_only': True},
        }

class ScanJobSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.display_name', read_only=True)
    class Meta:
        model = ScanJob
        fields = [
            'id','user','platform','platform_name','keywords','content_types','scan_frequency',
            'status','started_at','completed_at','total_items_scanned','error_message',
            'job_type','created_at'
        ]
        read_only_fields = [
            'id','user','status','started_at','completed_at','total_items_scanned',
            'error_message','job_type','created_at'
        ]

class ScanScheduleSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.display_name', read_only=True)
    class Meta:
        model = ScanSchedule
        fields = '__all__'

class ScannedContentSerializer(serializers.ModelSerializer):
    # Make platform writable so it won't be NULL in DB
    platform = serializers.PrimaryKeyRelatedField(queryset=Platform.objects.all())
    platform_name = serializers.CharField(source='platform.display_name', read_only=True)

    class Meta:
        model = ScannedContent
        fields = [
            'id','scan_job','platform','platform_name','platform_content_id','content_url',
            'content_type','title','description','author','author_url','published_at',
            'view_count','like_count','share_count','text_content','media_urls','metadata',
            'content_hash','created_at'
        ]
        read_only_fields = ['id','scan_job','platform_name','created_at']

    def _auto_hash(self, data: dict) -> str:
        base = "|".join([
            str(data.get('platform').pk if data.get('platform') else ''),
            data.get('platform_content_id') or '',
            data.get('content_url') or '',
            (data.get('text_content') or '')[:1000],
            data.get('title') or ''
        ])
        return hashlib.sha256(base.encode('utf-8')).hexdigest()

    def create(self, validated_data):
        # Accept JSON fields as strings
        if isinstance(validated_data.get('metadata'), str):
            try:
                validated_data['metadata'] = json.loads(validated_data['metadata'])
            except Exception:
                validated_data['metadata'] = {'raw': validated_data['metadata']}
        if isinstance(validated_data.get('media_urls'), str):
            try:
                validated_data['media_urls'] = json.loads(validated_data['media_urls'])
            except Exception:
                validated_data['media_urls'] = []

        # **Fallback:** if caller didn't send platform, default to 'telegram'
        if not validated_data.get('platform'):
            plat = Platform.objects.filter(name='telegram').first()
            if plat:
                validated_data['platform'] = plat

        # Auto-generate content_hash if missing
        if not validated_data.get('content_hash'):
            validated_data['content_hash'] = self._auto_hash(validated_data)

        return super().create(validated_data)
