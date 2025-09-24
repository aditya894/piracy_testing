from django.contrib import admin
from .models import Jurisdiction, DMCAClaim, CourtOrder, EvidenceLog, LegalCompliance
admin.site.register(Jurisdiction); admin.site.register(DMCAClaim); admin.site.register(CourtOrder); admin.site.register(EvidenceLog); admin.site.register(LegalCompliance)
