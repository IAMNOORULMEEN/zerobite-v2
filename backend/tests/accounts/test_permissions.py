from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import NGOProfile
from accounts.permissions import (
    IsAdminRole,
    IsDonor,
    IsNGO,
    IsVerifiedNGO,
    IsVolunteer,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


LOGIN_URL = reverse("accounts:login")


def make_user_and_tokens(
    client,
    *,
    email,
    password="Str0ngPass!234",
    role="DONOR",
):
    """Create a user and log them in; returns (user, access_token)."""
    user = User.objects.create_user(email=email, password=password, role=role)
    response = client.post(
        LOGIN_URL,
        {"email": email, "password": password},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    return user, response.json()["access"]


class _AnonUser:
    is_authenticated = False


def _request(user):
    return SimpleNamespace(user=user)


def _anonymous_request():
    return SimpleNamespace(user=_AnonUser())


# --- IsVerifiedNGO ---

def test_is_verified_ngo_denies_pending(client):
    user, _ = make_user_and_tokens(client, email="ngo-pending@example.com", role="NGO")
    NGOProfile.objects.create(
        user=user,
        organization_name="Pending Org",
        registration_number="REG-PENDING",
        status=NGOProfile.Status.PENDING,
    )

    assert IsVerifiedNGO().has_permission(_request(user), None) is False


def test_is_verified_ngo_denies_rejected(client):
    user, _ = make_user_and_tokens(client, email="ngo-rejected@example.com", role="NGO")
    NGOProfile.objects.create(
        user=user,
        organization_name="Rejected Org",
        registration_number="REG-REJECTED",
        status=NGOProfile.Status.REJECTED,
    )

    assert IsVerifiedNGO().has_permission(_request(user), None) is False


def test_is_verified_ngo_allows_approved(client):
    user, _ = make_user_and_tokens(client, email="ngo-approved@example.com", role="NGO")
    NGOProfile.objects.create(
        user=user,
        organization_name="Approved Org",
        registration_number="REG-APPROVED",
        status=NGOProfile.Status.APPROVED,
    )

    assert IsVerifiedNGO().has_permission(_request(user), None) is True


def test_is_verified_ngo_denies_donor(client):
    user, _ = make_user_and_tokens(client, email="donor-not-ngo@example.com", role="DONOR")

    assert IsVerifiedNGO().has_permission(_request(user), None) is False


# --- role-based classes ---

def test_role_permissions_allow_matching_role(client):
    donor, _ = make_user_and_tokens(client, email="perm-donor@example.com", role="DONOR")
    ngo, _ = make_user_and_tokens(client, email="perm-ngo@example.com", role="NGO")
    volunteer, _ = make_user_and_tokens(
        client, email="perm-vol@example.com", role="VOLUNTEER"
    )
    admin, _ = make_user_and_tokens(client, email="perm-admin@example.com", role="ADMIN")

    assert IsDonor().has_permission(_request(donor), None) is True
    assert IsNGO().has_permission(_request(ngo), None) is True
    assert IsVolunteer().has_permission(_request(volunteer), None) is True
    assert IsAdminRole().has_permission(_request(admin), None) is True


def test_role_permissions_deny_other_roles(client):
    donor, _ = make_user_and_tokens(client, email="cross-donor@example.com", role="DONOR")
    ngo, _ = make_user_and_tokens(client, email="cross-ngo@example.com", role="NGO")
    volunteer, _ = make_user_and_tokens(
        client, email="cross-vol@example.com", role="VOLUNTEER"
    )

    # Donor must not pass NGO/Volunteer/Admin checks and vice versa.
    assert IsNGO().has_permission(_request(donor), None) is False
    assert IsVolunteer().has_permission(_request(donor), None) is False
    assert IsAdminRole().has_permission(_request(donor), None) is False

    assert IsDonor().has_permission(_request(ngo), None) is False
    assert IsVolunteer().has_permission(_request(ngo), None) is False
    assert IsAdminRole().has_permission(_request(ngo), None) is False

    assert IsDonor().has_permission(_request(volunteer), None) is False
    assert IsNGO().has_permission(_request(volunteer), None) is False
    assert IsAdminRole().has_permission(_request(volunteer), None) is False


# --- anonymous ---

def test_all_permissions_deny_anonymous():
    request = _anonymous_request()
    for permission_cls in (IsDonor, IsNGO, IsVolunteer, IsAdminRole, IsVerifiedNGO):
        assert permission_cls().has_permission(request, None) is False
