import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_endpoint_returns_ok(client):
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_endpoint_does_not_require_auth(client):
    # The endpoint is public even when DRF defaults to IsAuthenticated.
    response = client.get("/api/health/")
    assert response.status_code == 200
