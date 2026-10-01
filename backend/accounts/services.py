"""Business logic for accounts. Views stay thin."""
from django.core.exceptions import ValidationError
from django.utils import timezone

from . import emails
from .models import NGOProfile


def approve_ngo(*, profile: NGOProfile, reviewer) -> NGOProfile:
    if profile.status != NGOProfile.Status.PENDING:
        raise ValidationError(
            {"status": "Only PENDING NGO profiles can be approved."}
        )

    profile.status = NGOProfile.Status.APPROVED
    profile.reviewed_by = reviewer
    profile.reviewed_at = timezone.now()
    profile.rejection_reason = ""
    profile.save(
        update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason"]
    )

    emails.send_ngo_decision_email(
        to_email=profile.user.email,
        organization_name=profile.organization_name,
        approved=True,
    )
    return profile


def reject_ngo(*, profile: NGOProfile, reviewer, reason: str) -> NGOProfile:
    if profile.status != NGOProfile.Status.PENDING:
        raise ValidationError(
            {"status": "Only PENDING NGO profiles can be rejected."}
        )

    reason = (reason or "").strip()
    if not reason:
        raise ValidationError({"reason": "A rejection reason is required."})

    profile.status = NGOProfile.Status.REJECTED
    profile.reviewed_by = reviewer
    profile.reviewed_at = timezone.now()
    profile.rejection_reason = reason
    profile.save(
        update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason"]
    )

    emails.send_ngo_decision_email(
        to_email=profile.user.email,
        organization_name=profile.organization_name,
        approved=False,
        reason=reason,
    )
    return profile
