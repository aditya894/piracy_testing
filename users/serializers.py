from rest_framework import serializers
from .models import User, ClientConfiguration, ActivityLog

class UserSerializer(serializers.ModelSerializer):
    class Meta: model=User; fields=['id','username','email','first_name','last_name','is_staff']

class ClientConfigurationSerializer(serializers.ModelSerializer):
    class Meta: model=ClientConfiguration; fields='__all__'

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta: model=ActivityLog; fields='__all__'
