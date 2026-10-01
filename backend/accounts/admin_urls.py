from django.urls import path

from .admin_views import NGOApproveView, NGOListView, NGORejectView

app_name = "accounts_admin"

urlpatterns = [
    path("ngos/", NGOListView.as_view(), name="ngo-list"),
    path("ngos/<int:pk>/approve/", NGOApproveView.as_view(), name="ngo-approve"),
    path("ngos/<int:pk>/reject/", NGORejectView.as_view(), name="ngo-reject"),
]
