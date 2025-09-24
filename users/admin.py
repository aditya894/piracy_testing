from django.contrib import admin
from .models import User, UserProfile, ClientConfiguration, ActivityLog
admin.site.register(User); admin.site.register(UserProfile); admin.site.register(ClientConfiguration); admin.site.register(ActivityLog)
