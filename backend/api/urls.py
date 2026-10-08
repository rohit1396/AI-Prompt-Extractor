from django.urls import path

from .views import (
    CsrfTokenView,
    ExtractionDetailView,
    ExtractionHistoryView,
    ExtractionUploadView,
    GoogleLoginView,
    LogoutView,
    MeView,
)

urlpatterns = [
    path('v1/auth/csrf/', CsrfTokenView.as_view(), name='auth-csrf'),
    path('v1/auth/google/', GoogleLoginView.as_view(), name='auth-google'),
    path('v1/auth/me/', MeView.as_view(), name='auth-me'),
    path('v1/auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('v1/extractions/', ExtractionUploadView.as_view(), name='extraction-upload'),
    path('v1/extractions/history/', ExtractionHistoryView.as_view(), name='extraction-history'),
    path('v1/extractions/<uuid:extraction_id>/', ExtractionDetailView.as_view(), name='extraction-detail'),
    path(
        'v1/extractions/<uuid:extraction_id>/status/',
        ExtractionDetailView.as_view(),
        name='extraction-status',
    ),
]
