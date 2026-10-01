from django.urls import reverse
from rest_framework import serializers

from .models import NGOProfile


class NGOReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    document_url = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="user.created_at", read_only=True)

    class Meta:
        model = NGOProfile
        fields = (
            "id",
            "user_email",
            "organization_name",
            "registration_number",
            "address",
            "status",
            "document_url",
            "created_at",
            "reviewed_at",
            "rejection_reason",
        )
        read_only_fields = fields

    def get_document_url(self, obj) -> str | None:
        """Return the admin-only streaming endpoint, never the raw media URL."""
        if not obj.verification_document:
            return None
        request = self.context.get("request")
        path = reverse("accounts_admin:ngo-document", args=[obj.pk])
        return request.build_absolute_uri(path) if request else path


class NGORejectSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=False, trim_whitespace=True)
