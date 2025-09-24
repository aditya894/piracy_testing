from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Jurisdiction(models.Model):
    name=models.CharField(max_length=100, unique=True)
    country_code=models.CharField(max_length=10, blank=True, null=True)
    description=models.TextField(blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: db_table='jurisdictions'; ordering=['name']
    def __str__(self): return self.name

class DMCAClaim(models.Model):
    STATUS=[('draft','Draft'),('submitted','Submitted'),('approved','Approved'),('rejected','Rejected'),('takedown_issued','Takedown Issued'),('disputed','Disputed'),('resolved','Resolved')]
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name='dmca_claims')
    content_match=models.ForeignKey('detection.ContentMatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='dmca_claims')
    title=models.CharField(max_length=500); description=models.TextField()
    original_content_url=models.URLField(blank=True, null=True); infringing_content_url=models.URLField()
    claimant_name=models.CharField(max_length=255); claimant_email=models.EmailField(); claimant_company=models.CharField(max_length=255, blank=True, null=True)
    declaration_of_accuracy=models.BooleanField(default=False); authorization_to_act=models.BooleanField(default=False); good_faith_belief=models.BooleanField(default=False)
    status=models.CharField(max_length=20, choices=STATUS, default='draft')
    submission_date=models.DateTimeField(blank=True, null=True); resolution_date=models.DateTimeField(blank=True, null=True)
    generated_document_path=models.CharField(max_length=1000, blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: db_table='dmca_claims'; ordering=['-created_at']
    def __str__(self): return f"DMCA Claim {self.id} - {self.title}"

class CourtOrder(models.Model):
    ORDER_TYPES=[('injunction','Injunction'),('subpoena','Subpoena'),('seizure','Seizure Order'),('other','Other')]
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name='court_orders')
    jurisdiction=models.ForeignKey(Jurisdiction, on_delete=models.SET_NULL, null=True, blank=True, related_name='court_orders')
    order_type=models.CharField(max_length=20, choices=ORDER_TYPES)
    case_number=models.CharField(max_length=100, unique=True); issuing_court=models.CharField(max_length=255)
    issue_date=models.DateField(); effective_date=models.DateField(blank=True, null=True); expiration_date=models.DateField(blank=True, null=True)
    summary=models.TextField(); full_document_path=models.FileField(upload_to='legal_documents/court_orders/', blank=True, null=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: db_table='court_orders'; ordering=['-issue_date']
    def __str__(self): return f"Court Order {self.case_number}"

class EvidenceLog(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name='evidence_logs')
    content_match=models.ForeignKey('detection.ContentMatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='evidence_logs')
    dmca_claim=models.ForeignKey('DMCAClaim', on_delete=models.SET_NULL, null=True, blank=True, related_name='evidence_logs')
    court_order=models.ForeignKey('CourtOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='evidence_logs')
    evidence_type=models.CharField(max_length=50); description=models.TextField(blank=True, null=True)
    file_path=models.FileField(upload_to='evidence/', blank=True, null=True); url_snapshot=models.URLField(blank=True, null=True)
    metadata=models.JSONField(default=dict); is_tamper_proof=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table='evidence_logs'; ordering=['-created_at']
    def __str__(self): return f"Evidence {self.id} - {self.evidence_type}"

class LegalCompliance(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE, related_name='legal_compliance')
    jurisdiction=models.ForeignKey(Jurisdiction, on_delete=models.CASCADE, related_name='compliance_records')
    is_compliant=models.BooleanField(default=True); last_checked=models.DateTimeField(auto_now=True)
    notes=models.TextField(blank=True, null=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: db_table='legal_compliance'; unique_together=[('user','jurisdiction')]; ordering=['-last_checked']
    def __str__(self): return f"{self.user.email} - {self.jurisdiction.name}"
