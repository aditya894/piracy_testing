import time, hashlib, requests
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from .models import Platform, ScanJob, ScannedContent, PlatformCredential
from users.models import User

class BasePlatformService:
    def __init__(self, platform_name: str, user: User):
        self.platform_name = platform_name
        self.user = user
        self.platform = Platform.objects.get(name=platform_name)
    def _get_credentials(self) -> Optional[PlatformCredential]:
        try: return PlatformCredential.objects.get(user=self.user, platform=self.platform)
        except PlatformCredential.DoesNotExist: return None
    def _generate_content_hash(self, content: str) -> str:
        return hashlib.sha256((content or '').encode('utf-8')).hexdigest()
    def scan_content(self, keywords: List[str], content_types: List[str]) -> List[Dict[str, Any]]: raise NotImplementedError
    def report_content(self, content_id: str, reason: str) -> Dict[str, Any]: raise NotImplementedError

class YouTubeService(BasePlatformService):
    def __init__(self, user: User):
        super().__init__('youtube', user)
        self.api_key = settings.PLATFORM_APIS.get('YOUTUBE_API_KEY')
        self.base_url = 'https://www.googleapis.com/youtube/v3'
    def scan_content(self, keywords: List[str], content_types: List[str]) -> List[Dict[str, Any]]:
        if not self.api_key: return []
        results = []
        for keyword in keywords:
            try:
                resp = requests.get(f"{self.base_url}/search", params={'part':'snippet','q':keyword,'type':'video','maxResults':10,'key':self.api_key}, timeout=10)
                resp.raise_for_status(); data = resp.json()
                for item in data.get('items', []):
                    results.append({
                        'platform_content_id': item['id']['videoId'],
                        'content_url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                        'content_type': 'video',
                        'title': item['snippet'].get('title',''),
                        'description': item['snippet'].get('description',''),
                        'author': item['snippet'].get('channelTitle',''),
                        'author_url': f"https://www.youtube.com/channel/{item['snippet'].get('channelId','')}",
                        'published_at': item['snippet'].get('publishedAt'),
                        'text_content': f"{item['snippet'].get('title','')} {item['snippet'].get('description','')}",
                        'metadata': {'channel_id': item['snippet'].get('channelId',''), 'thumbnail_url': item['snippet'].get('thumbnails',{}).get('default',{}).get('url',''), 'keyword_matched': keyword}
                    })
                time.sleep(0.1)
            except requests.RequestException:
                continue
        return results

class FacebookService(BasePlatformService):
    def __init__(self, user: User):
        super().__init__('facebook', user)
        self.access_token = settings.PLATFORM_APIS.get('FACEBOOK_ACCESS_TOKEN')
        self.base_url = 'https://graph.facebook.com/v19.0'
    def scan_content(self, keywords: List[str], content_types: List[str]) -> List[Dict[str, Any]]:
        return []  # integrate with Rights Manager or approved endpoints

class InstagramService(BasePlatformService):
    def __init__(self, user: User):
        super().__init__('instagram', user)
        self.access_token = settings.PLATFORM_APIS.get('INSTAGRAM_ACCESS_TOKEN')
    def scan_content(self, keywords: List[str], content_types: List[str]) -> List[Dict[str, Any]]:
        return []

class TelegramService(BasePlatformService):
    def __init__(self, user: User):
        super().__init__('telegram', user)
        self.bot_token = settings.PLATFORM_APIS.get('TELEGRAM_BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else ''
    def scan_content(self, keywords: List[str], content_types: List[str]) -> List[Dict[str, Any]]:
        return []

class PlatformServiceFactory:
    @staticmethod
    def get(platform_name: str, user: User) -> BasePlatformService:
        m={'youtube':YouTubeService,'facebook':FacebookService,'instagram':InstagramService,'telegram':TelegramService}
        if platform_name not in m: raise ValueError(f"Unsupported platform: {platform_name}")
        return m[platform_name](user)

class ScanJobManager:
    def __init__(self, user: User): self.user=user
    def execute_scan_job(self, scan_job: ScanJob):
        scan_job.status='running'; scan_job.started_at=timezone.now(); scan_job.save(update_fields=['status','started_at'])
        try:
            service = PlatformServiceFactory.get(scan_job.platform.name, scan_job.user)
            results = service.scan_content(scan_job.keywords, scan_job.content_types)
            objs=[]; 
            for r in results:
                content_hash = service._generate_content_hash(r.get('text_content',''))
                objs.append(ScannedContent(scan_job=scan_job, platform=scan_job.platform, platform_content_id=r['platform_content_id'], content_url=r['content_url'], content_type=r['content_type'], title=r.get('title',''), description=r.get('description',''), author=r.get('author',''), author_url=r.get('author_url',''), published_at=r.get('published_at'), view_count=r.get('view_count'), like_count=r.get('like_count'), share_count=r.get('share_count'), text_content=r.get('text_content',''), media_urls=r.get('media_urls',[]), metadata=r.get('metadata',{}), content_hash=content_hash))
            if objs: ScannedContent.objects.bulk_create(objs, ignore_conflicts=True)
            scan_job.status='completed'; scan_job.completed_at=timezone.now(); scan_job.total_items_scanned=len(objs); scan_job.save(update_fields=['status','completed_at','total_items_scanned'])
            return {'status':'success','items_found':len(objs)}
        except Exception as e:
            scan_job.status='failed'; scan_job.error_message=str(e); scan_job.completed_at=timezone.now(); scan_job.save(update_fields=['status','error_message','completed_at'])
            return {'status':'error','error':str(e)}
