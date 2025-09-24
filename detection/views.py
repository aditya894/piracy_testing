from rest_framework import viewsets, permissions
from .models import ProtectedContent, DetectionJob, ContentMatch, AIModel, FeedbackData
from .serializers import ProtectedContentSerializer, DetectionJobSerializer, ContentMatchSerializer, AIModelSerializer, FeedbackDataSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import ContentDetectionManager

class LLMTestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        owner = request.data.get("owner")
        candidate = request.data.get("candidate")
        platform = request.data.get("platform", "demo")
        url = request.data.get("url", "")
        if not owner or not candidate:
            return Response({"error": "owner and candidate are required"}, status=400)
        mgr = ContentDetectionManager(request.user)
        data = mgr.llm_match_judgement(owner, candidate, platform, url)
        return Response(data)

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes=[permissions.IsAuthenticated]

class ProtectedContentViewSet(BaseViewSet):
    queryset=ProtectedContent.objects.all(); serializer_class=ProtectedContentSerializer

class DetectionJobViewSet(BaseViewSet):
    queryset=DetectionJob.objects.all(); serializer_class=DetectionJobSerializer

class ContentMatchViewSet(BaseViewSet):
    queryset=ContentMatch.objects.all(); serializer_class=ContentMatchSerializer

class AIModelViewSet(BaseViewSet):
    queryset=AIModel.objects.all(); serializer_class=AIModelSerializer

class FeedbackDataViewSet(BaseViewSet):
    queryset=FeedbackData.objects.all(); serializer_class=FeedbackDataSerializer
