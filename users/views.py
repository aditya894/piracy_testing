from rest_framework import viewsets, permissions
from .models import User, ClientConfiguration, ActivityLog
from .serializers import UserSerializer, ClientConfigurationSerializer, ActivityLogSerializer

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes=[permissions.IsAuthenticated]

class UserViewSet(BaseViewSet):
    queryset=User.objects.all(); serializer_class=UserSerializer

class ClientConfigurationViewSet(BaseViewSet):
    queryset=ClientConfiguration.objects.all(); serializer_class=ClientConfigurationSerializer

class ActivityLogViewSet(BaseViewSet):
    queryset=ActivityLog.objects.all(); serializer_class=ActivityLogSerializer
