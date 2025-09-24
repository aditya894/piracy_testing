import os, hashlib
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import DMCAClaim, EvidenceLog

class LegalDocumentGenerator:
    def __init__(self, claim: DMCAClaim): self.claim=claim
    def generate_dmca_notice(self) -> str:
        context={'claim':self.claim, 'current_date': timezone.now().strftime('%Y-%m-%d'),
                 'protected_content': getattr(self.claim.content_match,'protected_content',None) if self.claim.content_match else None,
                 'infringing_content': getattr(self.claim.content_match,'scanned_content',None) if self.claim.content_match else None}
        md=render_to_string('legal/dmca_notice_template.md', context)
        dirp = settings.MEDIA_ROOT / 'legal_documents' / 'dmca'; os.makedirs(dirp, exist_ok=True)
        fname=f"dmca_notice_{self.claim.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.md"; fpath=dirp / fname
        with open(fpath, 'w', encoding='utf-8') as f: f.write(md)
        return str(fpath)

class EvidenceManager:
    def __init__(self, user): self.user=user
    def capture_web_snapshot(self, url: str, description: str=None, **refs):
        content_hash=hashlib.sha256(url.encode('utf-8')).hexdigest()
        evidence=EvidenceLog.objects.create(user=self.user, evidence_type='web_snapshot', description=description or f'Web snapshot of {url}',
                                            url_snapshot=url, metadata={'content_hash':content_hash, 'original_url':url}, **refs)
        return evidence
    def log_file_evidence(self, file_path: str, description: str=None, **refs):
        if not os.path.exists(file_path): raise FileNotFoundError(file_path)
        evidence=EvidenceLog.objects.create(user=self.user, evidence_type='file_upload', description=description or os.path.basename(file_path),
                                            file_path=file_path, metadata={'source':'uploaded'}, **refs)
        return evidence
