from django.db import models
from django.conf import settings


class SoftDeleteQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).active()


import uuid

class Institution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    official_name = models.CharField(max_length=255)
    aka = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    website = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = SoftDeleteManager()   # default → only active
    all_objects = models.Manager()  # optional → to also query deleted

    def __str__(self):
        return self.official_name


class InstitutionStaff(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="staff")
    title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    objects = SoftDeleteManager()   # default → only active
    all_objects = models.Manager()  # optional → to also query deleted

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Staff'}"


class Campus(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="campuses")
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    objects = SoftDeleteManager()   # default → only active
    all_objects = models.Manager()  # optional → to also query deleted

    def __str__(self):
        return f"{self.name} ({self.city})"


class Program(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='programs')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(help_text="Duration in months or years")
    language = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    objects = SoftDeleteManager()   # default → only active
    all_objects = models.Manager()  # optional → to also query deleted

    def __str__(self):
        return self.name


class ProgramIntake(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='intakes')
    start_month = models.CharField(max_length=20)
    application_deadline = models.DateField()
    seats = models.PositiveIntegerField()
    is_open = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    objects = SoftDeleteManager()   # default → only active
    all_objects = models.Manager()  # optional → to also query deleted

    def __str__(self):
        return f"{self.program.name} - {self.start_month}"





class ProgramFee(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='fees')
    tuition_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tuition_currency = models.CharField(max_length=3)
    application_fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    has_scholarship = models.BooleanField(default=False)
    scholarship_percent=models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    objects = SoftDeleteManager()   # default → only active
    all_objects = models.Manager()  # optional → to also query deleted

    def __str__(self):
        return f"Fees for {self.program.name}"
    
    def get_tuition_fee(self):
        if self.has_scholarship and self.scholarship_percent:
            return self.tuition_amount * (1 - self.scholarship_percent / 100)
        return self.tuition_amount


class ProgramFeature(models.Model):
    program = models.OneToOneField(Program, on_delete=models.CASCADE, primary_key=True, related_name='features')
    features = models.TextField()
    is_active = models.BooleanField(default=True)

    objects = SoftDeleteManager()   # default → only active
    all_objects = models.Manager()  # optional → to also query deleted

    def __str__(self):
        return f"Features for {self.program.name}"


class AdmissionRequirement(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='requirements')
    min_gpa = models.DecimalField(max_digits=4, decimal_places=2)
    other_requirements = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = SoftDeleteManager()   # default → only active
    all_objects = models.Manager()  # optional → to also query deleted

    def __str__(self):
        return f"Admission Requirements for {self.program.name}"


