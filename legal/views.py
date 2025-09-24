from rest_framework import viewsets, permissions
from .models import Jurisdiction, DMCAClaim, CourtOrder, EvidenceLog, LegalCompliance
from .serializers import JurisdictionSerializer, DMCAClaimSerializer, CourtOrderSerializer, EvidenceLogSerializer, LegalComplianceSerializer

class BaseViewSet(viewsets.ModelViewSet): permission_classes=[permissions.IsAuthenticated]
class JurisdictionViewSet(BaseViewSet): queryset=Jurisdiction.objects.all(); serializer_class=JurisdictionSerializer
class DMCAClaimViewSet(BaseViewSet): queryset=DMCAClaim.objects.all(); serializer_class=DMCAClaimSerializer
class CourtOrderViewSet(BaseViewSet): queryset=CourtOrder.objects.all(); serializer_class=CourtOrderSerializer
class EvidenceLogViewSet(BaseViewSet): queryset=EvidenceLog.objects.all(); serializer_class=EvidenceLogSerializer
class LegalComplianceViewSet(BaseViewSet): queryset=LegalCompliance.objects.all(); serializer_class=LegalComplianceSerializer
