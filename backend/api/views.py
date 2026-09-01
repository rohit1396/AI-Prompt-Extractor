import logging

from django.db import transaction
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
        with transaction.atomic():
            extraction = Extraction.objects.create(
                image=image,
                original_filename=image.name,
                file_size=image.size,
                content_type=image.content_type,
                status=Extraction.Status.RECEIVED,
                message='Image received.',
            )

            logger.info(
                'STEP 2: image saved extraction_id=%s filename=%s file_size=%s',
                extraction.id,
                image.name,
                image.size,
            )

            try:
                from .tasks import process_extraction

                extraction.status = Extraction.Status.QUEUED
                extraction.message = 'Image received. OCR job queued.'
                extraction.error_message = ''
                extraction.save(
                    update_fields=['status', 'message', 'error_message', 'updated_at'],
                )

                transaction.on_commit(lambda: process_extraction.delay(str(extraction.id)))
            except Exception as exc:
                logger.exception('Failed to queue extraction_id=%s', extraction.id)
                extraction.status = Extraction.Status.FAILED
                extraction.message = 'Unable to queue the OCR job.'
                extraction.error_message = str(exc) or 'Queueing OCR job failed.'
                extraction.save(
                    update_fields=['status', 'message', 'error_message', 'updated_at'],
                )

                payload = _serialize_extraction(extraction)
                response_serializer = ExtractionResponseSerializer(payload)
                return Response(response_serializer.data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

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
