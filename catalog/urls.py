from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register("institutions", InstitutionViewSet)
router.register("staff", InstitutionStaffViewSet)
router.register("campuses", CampusViewSet)
router.register("programs", ProgramViewSet)
router.register("intakes", ProgramIntakeViewSet)
router.register("fees", ProgramFeeViewSet)
router.register("features", ProgramFeatureViewSet)
router.register("requirements", AdmissionRequirementViewSet)

urlpatterns = router.urls
