from datetime import timedelta
import random
import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from cloudinary_storage.storage import MediaCloudinaryStorage


class Role(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    """
    A role is a type of user (e.g. student, agent, admin).
    """

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        # Assign default role "student" if no role was provided
        if not user.roles.exists():
            student_role, _ = Role.objects.get_or_create(
                code="student", defaults={"name": "Student"}
            )
            user.roles.add(student_role)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # UUID as primary key for modern microservice architecture
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                         help_text="UUID primary key for cross-service references")
    
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Many-to-Many relationship
    roles = models.ManyToManyField(Role, related_name="users", blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    def generate_otp(self):
        otp = str(random.randint(100000, 999999))
        self.otp = otp
        self.otp_created_at = timezone.now()
        self.save()
        return otp

    def is_otp_valid(self, otp):
        """Check if the OTP is correct and not expired (10 minutes)."""
        if self.otp != otp:
            return False
        if not self.otp_created_at:
            return False
        expiration_time = self.otp_created_at + timedelta(minutes=10)
        return timezone.now() <= expiration_time

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1,  choices=[("M", "Male"), ("F", "Female")], null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    avatar = models.ImageField(upload_to="career/avatars/",storage=MediaCloudinaryStorage(), null=True, blank=True)  # configure the media settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.email}"
    
class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    passport_number = models.CharField(unique=True, max_length=100, blank=True, null=True)
    national_id = models.CharField(unique=True, max_length=100, blank=True, null=True)
    current_level = models.CharField(max_length=100, choices=[("high school", "High School"),("undergraduate", "Undergraduate"), ("graduate", "Graduate"), ("phd", "PhD")], blank=True)
    target_countries = models.JSONField(default=list, blank=True)
    intended_major = models.CharField(max_length=100, blank=True)
    targeted_fields= models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Student: {self.user.email}"
    
    @property
    def uuid(self):
        """Return the user's UUID for cross-service references"""
        return self.user.id
    

class Agent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Agent: {self.user.email}"
    
