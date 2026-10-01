from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import DonorProfile, NGOProfile, VolunteerProfile

User = get_user_model()

ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2 MB


# --- Output serializers (read-only) ---

class DonorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorProfile
        fields = ("business_name", "donor_type", "address")
        read_only_fields = fields


class NGOProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NGOProfile
        fields = (
            "organization_name",
            "registration_number",
            "address",
            "verification_document",
            "status",
            "reviewed_at",
            "rejection_reason",
        )
        read_only_fields = fields


class VolunteerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerProfile
        fields = ("vehicle_type", "service_area")
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "phone",
            "role",
            "avatar",
            "created_at",
            "profile",
        )
        read_only_fields = fields

    def get_profile(self, obj):
        if obj.role == User.Role.DONOR and hasattr(obj, "donor_profile"):
            return DonorProfileSerializer(obj.donor_profile, context=self.context).data
        if obj.role == User.Role.NGO and hasattr(obj, "ngo_profile"):
            return NGOProfileSerializer(obj.ngo_profile, context=self.context).data
        if obj.role == User.Role.VOLUNTEER and hasattr(obj, "volunteer_profile"):
            return VolunteerProfileSerializer(obj.volunteer_profile, context=self.context).data
        return None


# --- Input serializers (validation only) ---

class RegisterSerializer(serializers.Serializer):
    """Flat input: user fields + role-specific profile fields."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=[
            User.Role.DONOR,
            User.Role.NGO,
            User.Role.VOLUNTEER,
        ]
    )

    # Donor fields
    business_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    donor_type = serializers.ChoiceField(
        choices=DonorProfile.DonorType.choices,
        required=False,
    )
    address = serializers.CharField(required=False, allow_blank=True)

    # NGO fields
    organization_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    registration_number = serializers.CharField(max_length=128, required=False, allow_blank=True)
    verification_document = serializers.FileField(required=False, allow_null=True)

    # Volunteer fields
    vehicle_type = serializers.ChoiceField(
        choices=VolunteerProfile.VehicleType.choices,
        required=False,
    )
    service_area = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        role = attrs["role"]

        if role == User.Role.NGO:
            required = ["organization_name", "registration_number"]
            missing = [f for f in required if not attrs.get(f)]
            if missing:
                raise serializers.ValidationError(
                    {f: "This field is required for NGO registration." for f in missing}
                )
            reg_num = attrs["registration_number"].strip()
            if NGOProfile.objects.filter(registration_number=reg_num).exists():
                raise serializers.ValidationError(
                    {"registration_number": "This registration number is already registered."}
                )
            attrs["registration_number"] = reg_num

        if role != User.Role.DONOR:
            for f in ("business_name", "donor_type"):
                attrs.pop(f, None)
        if role != User.Role.NGO:
            for f in ("organization_name", "registration_number", "verification_document"):
                attrs.pop(f, None)
        if role != User.Role.VOLUNTEER:
            for f in ("vehicle_type", "service_area"):
                attrs.pop(f, None)

        return attrs

    def create(self, validated_data):
        role = validated_data["role"]
        password = validated_data.pop("password")

        profile_fields = {
            "business_name": validated_data.pop("business_name", None),
            "donor_type": validated_data.pop("donor_type", None),
            "address": validated_data.pop("address", None),
            "organization_name": validated_data.pop("organization_name", None),
            "registration_number": validated_data.pop("registration_number", None),
            "verification_document": validated_data.pop("verification_document", None),
            "vehicle_type": validated_data.pop("vehicle_type", None),
            "service_area": validated_data.pop("service_area", None),
        }

        user = User.objects.create_user(password=password, **validated_data)
        user.role = role
        user.save(update_fields=["role"])

        if role == User.Role.DONOR:
            DonorProfile.objects.create(
                user=user,
                business_name=profile_fields["business_name"] or "",
                donor_type=profile_fields["donor_type"] or DonorProfile.DonorType.INDIVIDUAL,
                address=profile_fields["address"] or "",
            )
        elif role == User.Role.NGO:
            NGOProfile.objects.create(
                user=user,
                organization_name=profile_fields["organization_name"],
                registration_number=profile_fields["registration_number"],
                address=profile_fields["address"] or "",
                verification_document=profile_fields["verification_document"] or "",
            )
        elif role == User.Role.VOLUNTEER:
            VolunteerProfile.objects.create(
                user=user,
                vehicle_type=profile_fields["vehicle_type"] or VolunteerProfile.VehicleType.NONE,
                service_area=profile_fields["service_area"] or "",
            )

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserUpdateSerializer(serializers.ModelSerializer):
    """PATCH /api/auth/me/ — only editable user fields."""

    class Meta:
        model = User
        fields = ("full_name", "phone", "avatar")

    def validate_avatar(self, value):
        if value is None:
            return value
        content_type = getattr(value, "content_type", None)
        if content_type not in ALLOWED_AVATAR_TYPES:
            raise serializers.ValidationError(
                "Avatar must be a JPEG, PNG or WebP image."
            )
        if value.size > MAX_AVATAR_BYTES:
            raise serializers.ValidationError("Avatar must be 2 MB or smaller.")
        return value


# --- Password reset / change ---

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from the old one."}
            )
        return attrs
