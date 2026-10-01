from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Email-based user manager. No username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        DONOR = "DONOR", "Donor"
        NGO = "NGO", "NGO"
        VOLUNTEER = "VOLUNTEER", "Volunteer"
        ADMIN = "ADMIN", "Admin"

    username = None
    first_name = None
    last_name = None

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.DONOR,
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email


class DonorProfile(models.Model):
    class DonorType(models.TextChoices):
        RESTAURANT = "restaurant", "Restaurant"
        EVENT = "event", "Event"
        INDIVIDUAL = "individual", "Individual"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="donor_profile",
    )
    business_name = models.CharField(max_length=255, blank=True)
    donor_type = models.CharField(
        max_length=16,
        choices=DonorType.choices,
        default=DonorType.INDIVIDUAL,
    )
    address = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"DonorProfile<{self.user.email}>"


class NGOProfile(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="ngo_profile",
    )
    organization_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=128, unique=True)
    address = models.TextField(blank=True)
    verification_document = models.FileField(upload_to="ngo_docs/", blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ngo_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"NGOProfile<{self.organization_name}>"


class VolunteerProfile(models.Model):
    class VehicleType(models.TextChoices):
        NONE = "none", "None"
        BIKE = "bike", "Bike"
        CAR = "car", "Car"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="volunteer_profile",
    )
    vehicle_type = models.CharField(
        max_length=8,
        choices=VehicleType.choices,
        default=VehicleType.NONE,
    )
    service_area = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"VolunteerProfile<{self.user.email}>"
