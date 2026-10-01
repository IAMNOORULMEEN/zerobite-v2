from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


LOGIN_URL = reverse("accounts:login")
ME_URL = reverse("accounts:me")


@pytest.fixture
def temp_media(settings, tmp_path):
    """Point MEDIA_ROOT at a per-test tmp dir and restore afterwards."""
    original = settings.MEDIA_ROOT
    settings.MEDIA_ROOT = tmp_path
    try:
        yield tmp_path
    finally:
        settings.MEDIA_ROOT = original


def make_png_bytes(size=(4, 4)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, (0, 128, 255)).save(buf, format="PNG")
    return buf.getvalue()


def make_png_upload(name="avatar.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, make_png_bytes(), content_type="image/png")


def make_access_token(email="avatar@example.com") -> str:
    """Create a user and return a fresh access token via the login endpoint."""
    User.objects.create_user(email=email, password="Str0ngPass!234", role="DONOR")
    client = APIClient()
    response = client.post(
        LOGIN_URL,
        {"email": email, "password": "Str0ngPass!234"},
        format="json",
    )
    assert response.status_code == 200, response.content
    return response.json()["access"]


def test_patch_me_with_json_only_still_works(client):
    token = make_access_token(email="json@example.com")

    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api.patch(ME_URL, {"full_name": "JSON Only"}, format="json")

    assert response.status_code == 200, response.content
    assert response.json()["full_name"] == "JSON Only"


def test_avatar_upload_accepts_png(client, temp_media):
    token = make_access_token(email="png@example.com")

    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api.patch(ME_URL, {"avatar": make_png_upload()}, format="multipart")

    assert response.status_code == 200, response.content
    assert response.json()["avatar"]  # some URL

    user = User.objects.get(email="png@example.com")
    assert user.avatar.name.endswith(".png")


def test_avatar_upload_rejects_wrong_content_type(client, temp_media):
    token = make_access_token(email="badtype@example.com")

    fake = SimpleUploadedFile("evil.txt", b"hello", content_type="text/plain")

    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api.patch(ME_URL, {"avatar": fake}, format="multipart")

    assert response.status_code == 400
    assert "avatar" in response.json()


def test_avatar_upload_rejects_oversize(client, temp_media):
    token = make_access_token(email="big@example.com")

    big_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024 + 10)
    big = SimpleUploadedFile("big.png", big_bytes, content_type="image/png")

    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api.patch(ME_URL, {"avatar": big}, format="multipart")

    assert response.status_code == 400
    assert "avatar" in response.json()
