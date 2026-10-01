"""Thin wrappers around Django's mail helpers so tests patch one place."""
from django.conf import settings
from django.core.mail import send_mail


def send_ngo_decision_email(*, to_email: str, organization_name: str, approved: bool, reason: str = "") -> int:
    if approved:
        subject = "Your ZeroBite NGO account has been approved"
        body = (
            f"Hello {organization_name},\n\n"
            "Your NGO account has been approved. You can now reserve donations "
            "on ZeroBite.\n\n"
            "— The ZeroBite team"
        )
    else:
        subject = "Your ZeroBite NGO application was rejected"
        body = (
            f"Hello {organization_name},\n\n"
            "Unfortunately, your NGO application was rejected.\n\n"
            f"Reason: {reason}\n\n"
            "You may contact support if you believe this is a mistake.\n\n"
            "— The ZeroBite team"
        )

    return send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )


def send_password_reset_email(*, to_email: str, reset_url: str) -> int:
    subject = "Reset your ZeroBite password"
    body = (
        "We received a request to reset your ZeroBite password.\n\n"
        f"Reset it here: {reset_url}\n\n"
        "If you didn't request this, you can ignore this email.\n\n"
        "— The ZeroBite team"
    )
    return send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )
