from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

import pytest

User = get_user_model()

pytestmark = pytest.mark.django_db


RESET_URL = reverse("accounts:password-reset")
CONFIRM_URL = reverse("accounts:password-reset-confirm")
CHANGE_URL = reverse("accounts:change-password")
LOGIN_URL = reverse("accounts:login")


def make_user(email="reset@example.com", password="Str0ngPass!234"):
    return User.objects.create_user(email=email, password=password, role="DONOR")


def login(client, email, password="Str0ngPass!234"):
    response = client.post(
        LOGIN_URL,
        {"email": email, "password": password},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    return response.json()["access"]


# --- request ---

def test_password_reset_unknown_email_returns_same_200(client):
    response = client.post(
        RESET_URL,
        {"email": "nobody@example.com"},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert "detail" in response.json()
    # No email should have been sent.
    assert len(mail.outbox) == 0


def test_password_reset_known_email_sends_link(client):
    make_user()
    response = client.post(
        RESET_URL,
        {"email": "reset@example.com"},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert "/reset-password?uid=" in body
    assert "token=" in body


def test_password_reset_response_is_identical_for_known_and_unknown(client):
    make_user(email="known@example.com")
    known = client.post(
        RESET_URL, {"email": "known@example.com"}, content_type="application/json"
    )
    unknown = client.post(
        RESET_URL, {"email": "unknown@example.com"}, content_type="application/json"
    )
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()


# --- confirm ---

def _make_uid_token(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uid, token


def test_confirm_with_valid_token_changes_password(client):
    user = make_user(email="confirm@example.com")
    uid, token = _make_uid_token(user)

    response = client.post(
        CONFIRM_URL,
        {"uid": uid, "token": token, "new_password": "N3wStr0ng!456"},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    user.refresh_from_db()
    assert user.check_password("N3wStr0ng!456")


def test_confirm_rejects_invalid_token(client):
    user = make_user(email="badtoken@example.com")
    uid, _ = _make_uid_token(user)

    response = client.post(
        CONFIRM_URL,
        {"uid": uid, "token": "not-a-real-token", "new_password": "N3wStr0ng!456"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_confirm_rejects_reused_token(client):
    user = make_user(email="reuse@example.com")
    uid, token = _make_uid_token(user)

    first = client.post(
        CONFIRM_URL,
        {"uid": uid, "token": token, "new_password": "N3wStr0ng!456"},
        content_type="application/json",
    )
    assert first.status_code == 200, first.content

    # Same token must now be rejected (password changed invalidates it).
    second = client.post(
        CONFIRM_URL,
        {"uid": uid, "token": token, "new_password": "An0ther!789x"},
        content_type="application/json",
    )
    assert second.status_code == 400


def test_confirm_rejects_weak_password(client):
    user = make_user(email="weak@example.com")
    uid, token = _make_uid_token(user)

    response = client.post(
        CONFIRM_URL,
        {"uid": uid, "token": token, "new_password": "123"},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "new_password" in response.json()


# --- change password ---

def test_change_password_requires_auth(client):
    response = client.post(
        CHANGE_URL,
        {"old_password": "x", "new_password": "N3wStr0ng!456"},
        content_type="application/json",
    )
    assert response.status_code == 401


def test_change_password_updates_password(client):
    make_user(email="chg@example.com")
    token = login(client, "chg@example.com")

    response = client.post(
        CHANGE_URL,
        {"old_password": "Str0ngPass!234", "new_password": "N3wStr0ng!456"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200, response.content

    user = User.objects.get(email="chg@example.com")
    assert user.check_password("N3wStr0ng!456")


def test_change_password_rejects_wrong_old(client):
    make_user(email="wrongold@example.com")
    token = login(client, "wrongold@example.com")

    response = client.post(
        CHANGE_URL,
        {"old_password": "not-the-password", "new_password": "N3wStr0ng!456"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 400
    assert "old_password" in response.json()
