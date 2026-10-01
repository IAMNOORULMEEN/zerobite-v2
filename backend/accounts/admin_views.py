import mimetypes

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .admin_serializers import NGORejectSerializer, NGOReviewSerializer
from .models import NGOProfile
from .permissions import IsAdminRole
from .services import approve_ngo, reject_ngo


class NGOListView(ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = NGOReviewSerializer

    def get_queryset(self):
        status_param = self.request.query_params.get("status", NGOProfile.Status.PENDING)
        valid = {c for c, _ in NGOProfile.Status.choices}
        if status_param not in valid:
            raise ValidationError({"status": f"Must be one of: {sorted(valid)}."})
        return (
            NGOProfile.objects.select_related("user")
            .filter(status=status_param)
            .order_by("-user__created_at")
        )


class NGOApproveView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk: int):
        profile = get_object_or_404(NGOProfile, pk=pk)
        try:
            approve_ngo(profile=profile, reviewer=request.user)
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            )
        return Response(
            NGOReviewSerializer(profile, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class NGORejectView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, pk: int):
        profile = get_object_or_404(NGOProfile, pk=pk)
        serializer = NGORejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reject_ngo(
                profile=profile,
                reviewer=request.user,
                reason=serializer.validated_data["reason"],
            )
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            )
        return Response(
            NGOReviewSerializer(profile, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class NGODocumentView(APIView):
    """Admin-only download/stream of the NGO verification document.

    The raw media URL is never exposed by any serializer; admins fetch the file
    through this endpoint so access is gated by IsAdminRole.
    """

    permission_classes = [IsAdminRole]

    def get(self, request, pk: int):
        profile = get_object_or_404(NGOProfile, pk=pk)
        if not profile.verification_document:
            raise Http404("No verification document on file.")

        file_field = profile.verification_document
        try:
            file_field.open("rb")
        except FileNotFoundError as exc:
            raise Http404("Document file is missing.") from exc

        filename = file_field.name.rsplit("/", 1)[-1]
        content_type, _ = mimetypes.guess_type(filename)
        return FileResponse(
            file_field,
            as_attachment=False,
            filename=filename,
            content_type=content_type or "application/octet-stream",
        )
