from django.urls import path

from .views import ExtractionUploadView

urlpatterns = [
    path('v1/extractions/', ExtractionUploadView.as_view(), name='extraction-upload'),
]
