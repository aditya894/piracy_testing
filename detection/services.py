# detection/services.py
import hashlib
import random
from typing import Any, Dict

from django.utils import timezone

from .models import ProtectedContent, DetectionJob, ContentMatch, AIModel
from scanning.models import ScannedContent

# FIX: use the project package prefix so Python can find it
# was: from common.llm import OpenRouterClient, llm_json
from content_protection_platform.common.llm import OpenRouterClient, llm_json

from .prompt import (
    MATCH_DECISION_SYSTEM,
    MATCH_DECISION_USER_TEMPLATE,
    MATCH_DECISION_SCHEMA,
)

class BaseAIModelService:
    def __init__(self, model_type: str):
        self.model_type = model_type
        self.model = self._load_model()

    def _load_model(self):
        try:
            ai_model = AIModel.objects.get(
                model_type=self.model_type,
                is_active=True,
                is_default=True,
            )
            return {"name": ai_model.name, "version": ai_model.version}
        except AIModel.DoesNotExist:
            return None

    def generate_fingerprint(self, content: Any) -> Dict[str, Any]:
        raise NotImplementedError

    def compare_fingerprints(self, fp1: Dict[str, Any], fp2: Dict[str, Any]) -> float:
        raise NotImplementedError


class TextDetectionService(BaseAIModelService):
    def __init__(self):
        super().__init__("text")

    def generate_fingerprint(self, text: str):
        return (
            {"hash": hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]}
            if text
            else {}
        )

    def compare_fingerprints(self, fp1, fp2):
        if not fp1 or not fp2:
            return 0.0
        return 1.0 if fp1["hash"] == fp2["hash"] else random.uniform(0.5, 0.9)


class ImageDetectionService(BaseAIModelService):
    def __init__(self):
        super().__init__("image")

    def generate_fingerprint(self, image_url: str):
        return (
            {
                "hash": hashlib.sha256((image_url or "").encode("utf-8")).hexdigest()[
                    :16
                ]
            }
            if image_url
            else {}
        )

    def compare_fingerprints(self, fp1, fp2):
        if not fp1 or not fp2:
            return 0.0
        return 1.0 if fp1["hash"] == fp2["hash"] else random.uniform(0.5, 0.9)


class VideoDetectionService(BaseAIModelService):
    def __init__(self):
        super().__init__("video")

    def generate_fingerprint(self, video_url: str):
        return (
            {
                "hash": hashlib.sha256((video_url or "").encode("utf-8")).hexdigest()[
                    :16
                ]
            }
            if video_url
            else {}
        )

    def compare_fingerprints(self, fp1, fp2):
        if not fp1 or not fp2:
            return 0.0
        return 1.0 if fp1["hash"] == fp2["hash"] else random.uniform(0.5, 0.9)


class ContentDetectionManager:
    def __init__(self, user):
        self.user = user

    def _get_ai_service(self, t):
        return {
            "text": TextDetectionService,
            "image": ImageDetectionService,
            "video": VideoDetectionService,
        }.get(t, lambda: None)()

    def _initialize_default_ai_models(self):
        for t in ["text", "image", "video"]:
            AIModel.objects.get_or_create(
                model_type=t,
                is_default=True,
                defaults={
                    "name": f"Default {t.title()} Model",
                    "version": "1.0",
                    "is_active": True,
                    "description": f"Default {t} model",
                },
            )

    def run_detection(self, detection_job: DetectionJob):
        detection_job.status = "processing"
        detection_job.started_at = timezone.now()
        detection_job.save(update_fields=["status", "started_at"])
        try:
            scanned: ScannedContent = detection_job.scanned_content
            protected_qs = ProtectedContent.objects.filter(
                user=detection_job.user,
                is_active=True,
                monitoring_enabled=True,
                content_type__in=(detection_job.detection_types or ["text", "image", "video"]),
            )

            matches = 0
            high = 0

            for pc in protected_qs:
                svc = self._get_ai_service(pc.content_type)
                if not svc:
                    continue

                sim = 0.0
                if pc.content_type == "text" and scanned.text_content:
                    sim = svc.compare_fingerprints(
                        pc.text_fingerprint,
                        svc.generate_fingerprint(scanned.text_content),
                    )
                elif pc.content_type == "image" and scanned.media_urls:
                    sim = svc.compare_fingerprints(
                        pc.visual_fingerprint,
                        svc.generate_fingerprint(scanned.media_urls[0]),
                    )
                elif pc.content_type == "video" and scanned.content_url:
                    sim = svc.compare_fingerprints(
                        pc.audio_fingerprint,
                        svc.generate_fingerprint(scanned.content_url),
                    )

                if sim >= detection_job.similarity_threshold:
                    matches += 1
                    mt = "exact" if sim >= 0.9 else "partial"
                    if sim >= 0.9:
                        high += 1
                    ContentMatch.objects.create(
                        detection_job=detection_job,
                        protected_content=pc,
                        scanned_content=scanned,
                        match_type=mt,
                        similarity_score=sim,
                        confidence_level=("high" if sim >= 0.9 else "medium"),
                    )

            detection_job.status = "completed"
            detection_job.completed_at = timezone.now()
            detection_job.save(update_fields=["status", "completed_at"])
            return {
                "status": "success",
                "matches_found": matches,
                "high_confidence_matches": high,
            }
        except Exception as e:
            detection_job.status = "failed"
            detection_job.error_message = str(e)
            detection_job.completed_at = timezone.now()
            detection_job.save(update_fields=["status", "error_message", "completed_at"])
            return {"status": "error", "error": str(e)}

    def add_protected_content(
        self,
        user,
        title,
        content_type,
        text_content=None,
        file_path=None,
        external_url=None,
    ):
        if not (text_content or file_path or external_url):
            raise ValueError("Provide text_content, file_path, or external_url")

        content_hash = hashlib.sha256(
            f"{user.id}-{title}-{text_content or file_path or external_url}".encode(
                "utf-8"
            )
        ).hexdigest()

        text_fp = {}
        visual_fp = {}
        audio_fp = {}

        if content_type == "text" and text_content:
            text_fp = TextDetectionService().generate_fingerprint(text_content)
        elif content_type == "image" and (file_path or external_url):
            visual_fp = ImageDetectionService().generate_fingerprint(
                file_path or external_url
            )
        elif content_type == "video" and (file_path or external_url):
            vsvc = VideoDetectionService()
            isvc = ImageDetectionService()
            audio_fp = vsvc.generate_fingerprint(file_path or external_url)
            visual_fp = isvc.generate_fingerprint(file_path or external_url)

        pc = ProtectedContent.objects.create(
            user=user,
            title=title,
            content_type=content_type,
            text_content=text_content,
            file_path=file_path,
            external_url=external_url,
            content_hash=content_hash,
            text_fingerprint=text_fp,
            visual_fingerprint=visual_fp,
            audio_fingerprint=audio_fp,
        )
        return pc

    def update_protected_content(self, protected_content: ProtectedContent, **kwargs):
        for k, v in kwargs.items():
            setattr(protected_content, k, v)

        if any(k in kwargs for k in ["text_content", "file_path", "external_url"]):
            if protected_content.content_type == "text" and protected_content.text_content:
                protected_content.text_fingerprint = TextDetectionService().generate_fingerprint(
                    protected_content.text_content
                )
            elif protected_content.content_type == "image" and (
                protected_content.file_path or protected_content.external_url
            ):
                protected_content.visual_fingerprint = ImageDetectionService().generate_fingerprint(
                    protected_content.file_path or protected_content.external_url
                )
            elif protected_content.content_type == "video" and (
                protected_content.file_path or protected_content.external_url
            ):
                vsvc = VideoDetectionService()
                isvc = ImageDetectionService()
                protected_content.audio_fingerprint = vsvc.generate_fingerprint(
                    protected_content.file_path or protected_content.external_url
                )
                protected_content.visual_fingerprint = isvc.generate_fingerprint(
                    protected_content.file_path or protected_content.external_url
                )

        protected_content.save()
        return protected_content


def initialize_ai_models():
    ContentDetectionManager(user=None)._initialize_default_ai_models()
