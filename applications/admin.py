from django.contrib import admin
from .models import Application, ApplicationDocument,ApplicationRequiredDocument,ApplicationsEvent


# Register your models here.
@admin.register(Application)
class AppicationAdmin(admin.ModelAdmin):
    list_display = ("id", "student_id", "program_id", "status", "created_at")
    search_fields = ("id", "student_id", "program_id")
    
admin.site.register(ApplicationRequiredDocument)
admin.site.register(ApplicationDocument)
admin.site.register(ApplicationsEvent)