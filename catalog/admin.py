
from django.contrib import admin
from .models import Institution, InstitutionStaff, Campus, Program, ProgramIntake, ProgramFee, ProgramFeature, AdmissionRequirement

admin.site.register(Institution)
admin.site.register(InstitutionStaff)
admin.site.register(Campus)
admin.site.register(Program)
admin.site.register(ProgramIntake)
admin.site.register(ProgramFee)
admin.site.register(ProgramFeature)
admin.site.register(AdmissionRequirement)
