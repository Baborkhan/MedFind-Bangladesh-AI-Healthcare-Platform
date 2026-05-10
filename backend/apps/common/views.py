import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class HealthCheckView(APIView):
    permission_classes = [AllowAny]   # Public endpoint — no auth required

    def get(self, request):
        return Response({"status":"ok","service":"MedFind API","version":"1.0.0",
                         "timestamp": datetime.datetime.now().isoformat()})

