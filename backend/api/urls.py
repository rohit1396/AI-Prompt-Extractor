from django.urls import path

from .views import ExtractionDetailView, ExtractionUploadView

urlpatterns = [
    path('v1/extractions/', ExtractionUploadView.as_view(), name='extraction-upload'),
    path('v1/extractions/<uuid:extraction_id>/', ExtractionDetailView.as_view(), name='extraction-detail'),
    path(
        'v1/extractions/<uuid:extraction_id>/status/',
        ExtractionDetailView.as_view(),
        name='extraction-status',
    ),
]
