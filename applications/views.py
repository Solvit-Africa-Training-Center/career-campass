from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Application, ApplicationsEvent, Status
from .serializers import ApplicationCreateSerializer, ApplicationSerializer

# Create your views here.

def current_user_id(request) -> str:
    return request.headers.get("X-User-id", "00000000-0000-0000-0000-000000000001")

class ApplicationViewSet(viewsets.ViewSet):
    def list(self, request):
        student_id = current_user_id(request)
        qs = Application.objects.filter(student_id=student_id).order_by("-created_at")[:50]
        return Response([{"id": str(a.id), "status": a.status} for a in qs])
    
    def create(self, request):
        student_id = current_user_id(request)
        ser = ApplicationCreateSerializer(data = request.data)
        ser.is_valid(raise_exception=True)
        
        app = Application.objects.create(
            student_id = student_id,
            program_id = ser.validated_data["program_id"],
            intake_id = ser.validated_data["intake_id"],
            status = Status.DRAFT,
        )
        
        
        ApplicationsEvent.objects.create(
            application = app, 
            actor_id = student_id,
            event_type = "creates",
            to_status = Status.DRAFT,
            note = "Application created",
            
        )
        
        return Response(ApplicationSerializer(app).data, status=status.HTTP_201_CREATED)