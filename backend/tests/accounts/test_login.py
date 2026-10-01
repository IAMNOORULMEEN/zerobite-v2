import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

User = get_user_model()

pytestmark = pytest.mark.django_db


LOGIN_URL = reverse("accounts:login")
REFRESH_URL = reverse("accounts:refresh")
LOGOUT_URL = reverse("accounts:logout")


def _make_user(email="user@example.com", password="Str0ngPass!234", role="DONOR"):
    return User.objects.create_user(email=email, password=password, role=role)


def test_login_success_returns_tokens_and_user(client):
    _make_user()
    response = client.post(
        LOGIN_URL,
        {"email": "user@example.com", "password": "Str0ngPass!234"},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert "access" in body and "refresh" in body
    assert body["user"]["email"] == "user@example.com"
    assert body["user"]["role"] == "DONOR"
    assert body["user"]["ngo_status"] is None


def test_login_ngo_includes_ngo_status(client):
    user = _make_user(email="ngo@example.com", role="NGO")
    # Directly attach an NGO profile in PENDING state.
    from accounts.models import NGOProfile

    NGOProfile.objects.create(
        user=user,
        organization_name="Org",
        registration_number="REG-1",
    )

    response = client.post(
        LOGIN_URL,
        {"email": "ngo@example.com", "password": "Str0ngPass!234"},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    assert response.json()["user"]["ngo_status"] == "PENDING"


def test_login_wrong_password_returns_401(client):
    _make_user()
    response = client.post(
        LOGIN_URL,
        {"email": "user@example.com", "password": "wrong"},
        content_type="application/json",
    )
    assert response.status_code

