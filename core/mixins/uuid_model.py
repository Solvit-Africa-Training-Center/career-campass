import uuid
from django.db import models

class UUIDModelMixin:
    """
    A mixin for adding UUID as primary key to models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True
