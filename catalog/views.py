
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from .serializers import *
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Campus, Institution, InstitutionStaff, Program, ProgramIntake, ProgramFee, ProgramFeature, AdmissionRequirement

class SoftDeleteModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet:
    - Enforces soft delete via SoftDeleteMixin
    - Excludes PATCH (partial_update)
    """

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH")
    
    def destroy(self, request, *args, **kwargs):
        """
        Perform soft delete by setting is_active=False instead of removing the object.
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema(tags=["Campuses"], description="Retrieve, create, update or soft-delete campuses.")
class CampusViewSet(SoftDeleteModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Programs"], description="Retrieve, create, update or soft-delete programs.")
class ProgramViewSet(SoftDeleteModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Institutions"], description="Retrieve, create, update or soft-delete institutions.")
class InstitutionViewSet(SoftDeleteModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Institution Staff"], description="Retrieve, create, update or soft-delete institution staff.")
class InstitutionStaffViewSet(SoftDeleteModelViewSet):
    queryset = InstitutionStaff.objects.all()
    serializer_class = InstitutionStaffSerializer
    http_method_names = ["get", "post", "put", "delete"]





@extend_schema(tags=["Program Intakes"], description="Retrieve, create, update or soft-delete program intakes.")
class ProgramIntakeViewSet(SoftDeleteModelViewSet):
    queryset = ProgramIntake.objects.all()
    serializer_class = ProgramIntakeSerializer
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Program Fees"], description="Retrieve, create, update or soft-delete program fees.")
class ProgramFeeViewSet(SoftDeleteModelViewSet):
    queryset = ProgramFee.objects.all()
    serializer_class = ProgramFeeSerializer
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Program Features"], description="Retrieve, create, update or soft-delete program features.")
class ProgramFeatureViewSet(SoftDeleteModelViewSet):
    queryset = ProgramFeature.objects.all()
    serializer_class = ProgramFeatureSerializer
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Admission Requirements"], description="Retrieve, create, update or soft-delete admission requirements.")
class AdmissionRequirementViewSet(SoftDeleteModelViewSet):
    queryset = AdmissionRequirement.objects.all()
    serializer_class = AdmissionRequirementSerializer
    http_method_names = ["get", "post", "put", "delete"]
