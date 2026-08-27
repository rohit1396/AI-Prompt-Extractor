import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Extraction
from .serializers import ExtractionResponseSerializer, ImageUploadSerializer

logger = logging.getLogger(__name__)


class ExtractionUploadView(APIView):
    def post(self, request):
        logger.info(
            'STEP 1: request received method=%s path=%s content_type=%s',
            request.method,
            request.path,
            request.content_type,
        )

        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = serializer.validated_data['image']
        # OCR is intentionally deferred to a future worker so this request only
        # validates and stores the upload.
        extraction = Extraction.objects.create(
            image=image,
            original_filename=image.name,
            file_size=image.size,
            content_type=image.content_type,
            status=Extraction.Status.RECEIVED,
            message='Image received. OCR will be processed asynchronously.',
        )

        logger.info(
            'STEP 2: image saved extraction_id=%s filename=%s file_size=%s',
            extraction.id,
            image.name,
            image.size,
        )

        payload = _serialize_extraction(extraction)
        response_serializer = ExtractionResponseSerializer(payload)
        logger.info(
            'STEP 3: upload accepted extraction_id=%s status_code=%s',
            extraction.id,
            status.HTTP_201_CREATED,
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ExtractionDetailView(APIView):
    def get(self, request, extraction_id):
        extraction = get_object_or_404(Extraction, pk=extraction_id)
        payload = _serialize_extraction(extraction)
        response_serializer = ExtractionResponseSerializer(payload)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


def _serialize_extraction(extraction: Extraction) -> dict[str, object]:
    return {
        'id': str(extraction.id),
        'status': extraction.status,
        'filename': extraction.original_filename,
        'content_type': extraction.content_type,
        'file_size': extraction.file_size,
        'extracted_text': extraction.extracted_text,
        'message': extraction.message,
        'error_message': extraction.error_message,
        'processing_time_ms': extraction.processing_time_ms,
        'created_at': extraction.created_at,
        'updated_at': extraction.updated_at,
    }
