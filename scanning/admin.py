from django.contrib import admin
from .models import Platform, ScanJob, ScannedContent, ScanSchedule, PlatformCredential
admin.site.register(Platform); admin.site.register(ScanJob); admin.site.register(ScannedContent); admin.site.register(ScanSchedule); admin.site.register(PlatformCredential)
