import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

pytestmark = pytest.mark.django_db


LOGIN_URL = reverse("accounts:login")
REFRESH_URL = reverse("accounts:refresh")
LOGOUT_URL = reverse("accounts:logout")
ME_URL = reverse("accounts:me")


def make_user_and_tokens(
    client,
    *,
    email="session@example.com",
    password="Str0ngPass!234",
    role="DONOR",
):
    """Create a user, log them in via the login endpoint, return (user, tokens)."""
    user = User.objects.create_user(email=email, password=password, role=role)
    response = client.post(
        LOGIN_URL,
        {"email": email, "password": password},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    return user, {"access": body["access"], "refresh": body["refresh"]}


def auth_header(tokens):
    return {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}


# --- refresh ---

def test_refresh_with_valid_token_returns_new_access(client):
    _, tokens = make_user_and_tokens(client)

    response = client.post(
        REFRESH_URL,
        {"refresh": tokens["refresh"]},
        content_type="application/json",
    )

    assert response.status_code == 200, response.content
    assert "access" in response.json()


def test_refresh_with_invalid_token_returns_401(client):
    response = client.post(
        REFRESH_URL,
        {"refresh": "not-a-real-token"},
        content_type="application/json",
    )
    assert response.status_code == 401


# --- logout ---

def test_logout_blacklists_refresh_token(client):
    _, tokens = make_user_and_tokens(client, email="logout@example.com")

    response = client.post(
        LOGOUT_URL,
        {"refresh": tokens["refresh"]},
        content_type="application/json",
        **auth_header(tokens),
    )
    assert response.status_code == 205, response.content

    # The same refresh token must no longer work.
    refresh_response = client.post(
        REFRESH_URL,
        {"refresh": tokens["refresh"]},
        content_type="application/json",
    )
    assert refresh_response.status_code == 401


def test_logout_without_authentication_returns_401(client):
    # No Authorization header even though we send a refresh token.
    response = client.post(
        LOGOUT_URL,
        {"refresh": "whatever"},
        content_type="application/json",
    )
    assert response.status_code == 401


# --- me ---

def test_me_without_token_returns_401(client):
    response = client.get(ME_URL)
    assert response.status_code == 401


def test_me_with_token_returns_current_user_without_password(client):
    user, tokens = make_user_and_tokens(client, email="me@example.com", role="DONOR")

    response = client.get(ME_URL, **auth_header(tokens))
    assert response.status_code == 200, response.content
    body = response.json()

    assert body["id"] == user.id
    assert body["email"] == user.email
    assert body["role"] == "DONOR"
    assert "password" not in body


def test_me_patch_updates_full_name(client):
    _, tokens = make_user_and_tokens(client, email="patch@example.com")

    response = client.patch(
        ME_URL,
        {"full_name": "New Name"},
        content_type="application/json",
        **auth_header(tokens),
    )
    assert response.status_code == 200, response.content
    assert response.json()["full_name"] == "New Name"


def test_me_patch_cannot_change_role(client):
    user, tokens = make_user_and_tokens(client, email="norole@example.com", role="DONOR")

    response = client.patch(
        ME_URL,
        {"role": "ADMIN", "full_name": "Sneaky"},
        content_type="application/json",
        **auth_header(tokens),
    )
    assert response.status_code == 200, response.content

    user.refresh_from_db()
    assert user.role == "DONOR"
    # full_name change should still apply.
    assert user.full_name == "Sneaky"
