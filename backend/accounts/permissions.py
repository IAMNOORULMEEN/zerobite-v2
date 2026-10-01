from rest_framework.permissions import BasePermission

from .models import NGOProfile, User


class _RolePermission(BasePermission):
    role: str | None = None

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and self.role is not None
            and user.role == self.role
        )


class IsDonor(_RolePermission):
    role = User.Role.DONOR


class IsNGO(_RolePermission):
    role = User.Role.NGO


class IsVolunteer(_RolePermission):
    role = User.Role.VOLUNTEER


class IsAdminRole(_RolePermission):
    role = User.Role.ADMIN


class IsVerifiedNGO(BasePermission):
    """Role == NGO AND the NGO profile has been APPROVED by an admin."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or user.role != User.Role.NGO:
            return False
        profile = getattr(user, "ngo_profile", None)
        return bool(profile and profile.status == NGOProfile.Status.APPROVED)
