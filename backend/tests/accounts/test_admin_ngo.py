from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from accounts.models import NGOProfile

User = get_user_model()

pytestmark = pytest.mark.django_db


LOGIN_URL = reverse("accounts:login")
NGO_LIST_URL = reverse("accounts_admin:ngo-list")


def make_png_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (2, 2), (255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


def make_png_upload(name: str = "doc.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, make_png_bytes(), content_type="image/png")


def login(client, *, email, password="Str0ngPass!234", role="DONOR"):
    User.objects.create_user(email=email, password=password, role=role)
    response = client.post(
        LOGIN_URL,
        {"email": email, "password": password},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    return response.json()["access"]


def auth_header(token: str) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def make_ngo(email: str, *, status=NGOProfile.Status.PENDING, reg: str = "REG-1"):
    user = User.objects.create_user(
        email=email, password="Str0ngPass!234", role="NGO"
    )
    return NGOProfile.objects.create(
        user=user,
        organization_name="Org",
        registration_number=reg,
        status=status,
        verification_document=make_png_upload(),
    )


# --- list ---

def test_admin_lists_pending_ngos(client):
    admin_token = login(client, email="admin@example.com", role="ADMIN")
    make_ngo("pending@example.com")
    make_ngo(
        "approved@example.com",
        status=NGOProfile.Status.APPROVED,
        reg="REG-2",
    )

    response = client.get(NGO_LIST_URL, **auth_header(admin_token))
    assert response.status_code == 200, response.content
    body = response.json()
    # Default filter is PENDING.
    results = body["results"]
    assert len(results) == 1
    assert results[0]["user_email"] == "pending@example.com"
    assert results[0]["status"] == "PENDING"


def test_admin_list_filters_by_status(client):
    admin_token = login(client, email="admin2@example.com", role="ADMIN")
    make_ngo("p@example.com")
    make_ngo("a@example.com", status=NGOProfile.Status.APPROVED, reg="REG-A")

    response = client.get(NGO_LIST_URL + "?status=APPROVED", **auth_header(admin_token))
    assert response.status_code == 200, response.content
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["user_email"] == "a@example.com"


def test_admin_list_returns_document_endpoint_not_raw_media_url(client):
    admin_token = login(client, email="admin3@example.com", role="ADMIN")
    profile = make_ngo("doc@example.com")

    response = client.get(NGO_LIST_URL, **auth_header(admin_token))
    assert response.status_code == 200
    row = response.json()["results"][0]

    expected_path = reverse("accounts_admin:ngo-document", args=[profile.pk])
    assert row["document_url"].endswith(expected_path)
    # The raw media URL must NOT appear.
    assert "/media/" not in row["document_url"]


def test_non_admin_gets_403_on_list(client):
    donor_token = login(client, email="d@example.com", role="DONOR")
    response = client.get(NGO_LIST_URL, **auth_header(donor_token))
    assert response.status_code == 403


# --- approve / reject ---

def test_admin_approves_pending_ngo(client):
    admin_token = login(client, email="approver@example.com", role="ADMIN")
    profile = make_ngo("apprv@example.com")

    url = reverse("accounts_admin:ngo-approve", args=[profile.pk])
    response = client.post(url, **auth_header(admin_token))

    assert response.status_code == 200, response.content
    profile.refresh_from_db()
    assert profile.status == NGOProfile.Status.APPROVED
    assert profile.reviewed_by is not None
    assert profile.reviewed_at is not None

    assert len(mail.outbox) == 1
    assert "approved" in mail.outbox[0].subject.lower()


def test_admin_rejects_pending_ngo_with_reason(client):
    admin_token = login(client, email="rejecter@example.com", role="ADMIN")
    profile = make_ngo("rej@example.com")

    url = reverse("accounts_admin:ngo-reject", args=[profile.pk])
    response = client.post(
        url,
        {"reason": "Documents incomplete."},
        content_type="application/json",
        **auth_header(admin_token),
    )

    assert response.status_code == 200, response.content
    profile.refresh_from_db()
    assert profile.status == NGOProfile.Status.REJECTED
    assert profile.rejection_reason == "Documents incomplete."
    assert profile.reviewed_by is not None
    assert len(mail.outbox) == 1
    assert "rejected" in mail.outbox[0].subject.lower()


def test_reject_without_reason_returns_400(client):
    admin_token = login(client, email="rejecter2@example.com", role="ADMIN")
    profile = make_ngo("rej2@example.com")

    url = reverse("accounts_admin:ngo-reject", args=[profile.pk])
    response = client.post(
        url,
        {"reason": "   "},
        content_type="application/json",
        **auth_header(admin_token),
    )
    assert response.status_code == 400


def test_approving_non_pending_ngo_returns_400(client):
    admin_token = login(client, email="approver2@example.com", role="ADMIN")
    profile = make_ngo(
        "already@example.com",
        status=NGOProfile.Status.APPROVED,
        reg="REG-DONE",
    )

    url = reverse("accounts_admin:ngo-approve", args=[profile.pk])
    response = client.post(url, **auth_header(admin_token))
    assert response.status_code == 400


def test_rejecting_non_pending_ngo_returns_400(client):
    admin_token = login(client, email="rejecter3@example.com", role="ADMIN")
    profile = make_ngo(
        "rejdone@example.com",
        status=NGOProfile.Status.REJECTED,
        reg="REG-REJ",
    )

    url = reverse("accounts_admin:ngo-reject", args=[profile.pk])
    response = client.post(
        url,
        {"reason": "again"},
        content_type="application/json",
        **auth_header(admin_token),
    )
    assert response.status_code == 400


def test_non_admin_gets_403_on_approve(client):
    donor_token = login(client, email="d2@example.com", role="DONOR")
    profile = make_ngo("noperm@example.com")

    url = reverse("accounts_admin:ngo-approve", args=[profile.pk])
    response = client.post(url, **auth_header(donor_token))
    assert response.status_code == 403


# --- document streaming ---

def test_admin_can_stream_document(client):
    admin_token = login(client, email="docadmin@example.com", role="ADMIN")
    profile = make_ngo("stream@example.com")

    url = reverse("accounts_admin:ngo-document", args=[profile.pk])
    response = client.get(url, **auth_header(admin_token))

    assert response.status_code == 200
    assert response["Content-Type"].startswith("image/png")
    body = b"".join(response.streaming_content)
    assert body.startswith(b"\x89PNG")


def test_non_admin_cannot_stream_document(client):
    donor_token = login(client, email="docdonor@example.com", role="DONOR")
    profile = make_ngo("stream2@example.com")

    url = reverse("accounts_admin:ngo-document", args=[profile.pk])
    response = client.get(url, **auth_header(donor_token))
    assert response.status_code == 403


def test_document_404_when_missing(client):
    admin_token = login(client, email="docadmin2@example.com", role="ADMIN")
    user = User.objects.create_user(
        email="nodoc@example.com", password="Str0ngPass!234", role="NGO"
    )
    profile = NGOProfile.objects.create(
        user=user,
        organization_name="NoDoc",
        registration_number="REG-NODOC",
    )
    url = reverse("accounts_admin:ngo-document", args=[profile.pk])
    response = client.get(url, **auth_header(admin_token))
    assert response.status_code == 404
