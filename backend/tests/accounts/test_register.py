import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import DonorProfile, NGOProfile, VolunteerProfile

User = get_user_model()

pytestmark = pytest.mark.django_db


REGISTER_URL = reverse("accounts:register")


def test_register_donor_creates_user_and_profile(client):
    payload = {
        "email": "donor@example.com",
        "password": "Str0ngPass!234",
        "full_name": "Dana Donor",
        "phone": "+10000000000",
        "role": "DONOR",
        "business_name": "Dana's Diner",
        "donor_type": "restaurant",
        "address": "1 Main St",
    }
    response = client.post(REGISTER_URL, payload, content_type="application/json")

    assert response.status_code == 201, response.content
    body = response.json()
    assert body["email"] == "donor@example.com"
    assert body["role"] == "DONOR"
    assert "password" not in body

    user = User.objects.get(email="donor@example.com")
    assert user.check_password("Str0ngPass!234")
    assert user.donor_profile.business_name == "Dana's Diner"
    assert user.donor_profile.donor_type == "restaurant"


def test_register_ngo_creates_pending_profile(client):
    payload = {
        "email": "ngo@example.com",
        "password": "Str0ngPass!234",
        "full_name": "Nina NGO",
        "role": "NGO",
        "organization_name": "Helping Hands",
        "registration_number": "REG-12345",
        "address": "2 Side St",
    }
    response = client.post(REGISTER_URL, payload, content_type="application/json")

    assert response.status_code == 201, response.content
    user = User.objects.get(email="ngo@example.com")
    assert user.role == "NGO"
    assert user.ngo_profile.status == NGOProfile.Status.PENDING
    assert user.ngo_profile.registration_number == "REG-12345"


def test_register_volunteer_creates_profile(client):
    payload = {
        "email": "vol@example.com",
        "password": "Str0ngPass!234",
        "full_name": "Vic Volunteer",
        "role": "VOLUNTEER",
        "vehicle_type": "bike",
        "service_area": "Downtown",
    }
    response = client.post(REGISTER_URL, payload, content_type="application/json")

    assert response.status_code == 201, response.content
    user = User.objects.get(email="vol@example.com")
    assert user.role == "VOLUNTEER"
    assert user.volunteer_profile.vehicle_type == "bike"


def test_register_admin_role_is_rejected(client):
    payload = {
        "email": "admin@example.com",
        "password": "Str0ngPass!234",
        "role": "ADMIN",
    }
    response = client.post(REGISTER_URL, payload, content_type="application/json")
    assert response.status_code == 400
    assert "role" in response.json()


def test_register_duplicate_email_is_rejected(client):
    User.objects.create_user(
        email="dup@example.com",
        password="Str0ngPass!234",
        role="DONOR",
    )
    payload = {
        "email": "dup@example.com",
        "password": "Str0ngPass!234",
        "role": "DONOR",
    }
    response = client.post(REGISTER_URL, payload, content_type="application/json")
    assert response.status_code == 400
    assert "email" in response.json()


def test_register_weak_password_is_rejected(client):
    payload = {
        "email": "weak@example.com",
        "password": "123",
        "role": "DONOR",
    }
    response = client.post(REGISTER_URL, payload, content_type="application/json")
    assert response.status_code == 400
    assert "password" in response.json()


def test_register_ngo_missing_registration_number_is_rejected(client):
    payload = {
        "email": "ngo2@example.com",
        "password": "Str0ngPass!234",
        "role": "NGO",
        "organization_name": "No Reg",
    }
    response = client.post(REGISTER_URL, payload, content_type="application/json")
    assert response.status_code == 400
    assert "registration_number" in response.json()


def test_register_ngo_duplicate_registration_number_is_rejected(client):
    NGOProfile.objects.create(
        user=User.objects.create_user(
            email="ngo-existing@example.com",
            password="Str0ngPass!234",
            role="NGO",
        ),
        organization_name="Existing",
        registration_number="REG-DUP",
    )
    payload = {
        "email": "ngo-new@example.com",
        "password": "Str0ngPass!234",
        "role": "NGO",
        "organization_name": "New",
        "registration_number": "REG-DUP",
    }
    response = client.post(REGISTER_URL, payload, content_type="application/json")
    assert response.status_code == 400
    assert "registration_number" in response.json()
