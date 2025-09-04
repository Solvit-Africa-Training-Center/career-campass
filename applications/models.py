from django.db import models
import uuid
from django.utils import timezone

class Status(models.TextChoices):
    DRAFT = "Draft", "Draft"
    SUBMITTED  = "Sbmitted", "Submitted"
    UNDER_REVIEW = "UnderReview", "Under Review"
    OFFER = "Offer", "Offer"
    CONDITIONAL_OFFER = "ConditionalOffer", "Conditional Offer"
    REJECTED = "Rejected", "Rejected"
    ACCEPTED = "Accepted", "Accepted"
    WITHDRAWN = "Withdrawn", "Withdrawn"
    
    
class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.UUIDField()
    program_id = models.UUIDField()
    intake_id = models.UUIDField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["student_id"]),
            models.Index(fields = ["program_id"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]

class ApplicationRequiredDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name = "required_docs")
    doc_type_id = models.UUIDField()
    is_mandatory = models.BooleanField(default=True)
    min_items = models.PositiveIntegerField(default=1)
    max_items = models.PositiveIntegerField(default=1)
    source = models.CharField(max_length=16)
    source_required_document_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["application", "doc_type_id"], name = "uq_app_reqdoc_app_doctype")
        ]
        
        indexes = [models.Index(fields=["application"])]

class ApplicationDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="documents")
    doc_type_id = models.UUIDField()
    student_document_id = models.UUIDField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    
    class Meta:
        indexes = [
            models.Index(fields=["application"]),
            models.Index(fields=["doc_type_id"]),
        ]

class ApplicationsEvent(models.Model):
    id = models.UUIDField(primary_key=True, default = uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="events" )
    actor_id = models.UUIDField()
    event_type = models.CharField(max_length=32)
    from_status = models.CharField(max_length=32, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default = timezone.now, editable=False)
    
    class Meta:
        indexes = [models.Index(fields=["application"])]
        ordering = ["created_at"]