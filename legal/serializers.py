from rest_framework import serializers
from .models import Jurisdiction, DMCAClaim, CourtOrder, EvidenceLog, LegalCompliance

class JurisdictionSerializer(serializers.ModelSerializer):
    class Meta: model=Jurisdiction; fields='__all__'

class DMCAClaimSerializer(serializers.ModelSerializer):
    user_email=serializers.CharField(source='user.email', read_only=True)
    class Meta: model=DMCAClaim; fields='__all__'; read_only_fields=['generated_document_path','submission_date','resolution_date']

class CourtOrderSerializer(serializers.ModelSerializer):
    user_email=serializers.CharField(source='user.email', read_only=True)
    jurisdiction_name=serializers.CharField(source='jurisdiction.name', read_only=True)
    class Meta: model=CourtOrder; fields='__all__'

class EvidenceLogSerializer(serializers.ModelSerializer):
    user_email=serializers.CharField(source='user.email', read_only=True)
    class Meta: model=EvidenceLog; fields='__all__'; read_only_fields=['created_at']

class LegalComplianceSerializer(serializers.ModelSerializer):
    user_email=serializers.CharField(source='user.email', read_only=True)
    jurisdiction_name=serializers.CharField(source='jurisdiction.name', read_only=True)
    class Meta: model=LegalCompliance; fields='__all__'; read_only_fields=['last_checked','created_at','updated_at']
