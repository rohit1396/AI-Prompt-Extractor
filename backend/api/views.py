import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .cloudinary import cloudinary_is_enabled, delete_image_from_cloudinary, upload_image_to_cloudinary
from .models import Extraction
from .serializers import ExtractionHistorySerializer, ExtractionResponseSerializer, ImageUploadSerializer

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
        cloudinary_upload = None
        if cloudinary_is_enabled():
            try:
                cloudinary_upload = upload_image_to_cloudinary(image)
            except Exception as exc:
                logger.exception('Failed to upload image to Cloudinary')
                return Response(
                    {
                        'detail': str(exc) or 'Unable to store the uploaded image.',
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        try:
            with transaction.atomic():
                extraction = Extraction.objects.create(
                    image=None if cloudinary_upload else image,
                    storage_provider=(
                        Extraction.StorageProvider.CLOUDINARY
                        if cloudinary_upload
                        else Extraction.StorageProvider.LOCAL
                    ),
                    cloudinary_public_id=cloudinary_upload.public_id if cloudinary_upload else '',
                    cloudinary_secure_url=cloudinary_upload.secure_url if cloudinary_upload else '',
                    cloudinary_version=cloudinary_upload.version if cloudinary_upload else None,
                    original_filename=image.name,
                    file_size=image.size,
                    content_type=image.content_type,
                    status=Extraction.Status.RECEIVED,
                    message='Image received.',
                )
        except Exception:
            if cloudinary_upload:
                delete_image_from_cloudinary(cloudinary_upload.public_id)
            logger.exception('Failed to persist extraction record')
            return Response(
                {
                    'detail': 'Unable to persist the uploaded image.',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
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


class ExtractionHistoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class ExtractionHistoryView(APIView):
    def get(self, request):
        queryset = Extraction.objects.order_by('-created_at', '-id')
        paginator = ExtractionHistoryPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ExtractionHistorySerializer(
            [_history_payload(extraction) for extraction in page],
            many=True,
        )
        return paginator.get_paginated_response(serializer.data)


def _serialize_extraction(extraction: Extraction) -> dict[str, object]:
    image_url = extraction.cloudinary_secure_url
    if not image_url and extraction.image:
        try:
            image_url = extraction.image.url
        except Exception:
            image_url = ''

    return {
        'id': str(extraction.id),
        'status': extraction.status,
        'filename': extraction.original_filename,
        'content_type': extraction.content_type,
        'file_size': extraction.file_size,
        'image_url': image_url,
        'storage_provider': extraction.storage_provider,
        'cloudinary_public_id': extraction.cloudinary_public_id,
        'extracted_text': extraction.extracted_text,
        'is_prompt': extraction.classification_label == Extraction.ClassificationLabel.PROMPT,
        'prompt_confidence': extraction.classification_confidence,
        'raw_ocr_text': extraction.raw_ocr_text,
        'classification_label': extraction.classification_label,
        'classification_score': extraction.classification_score,
        'classification_confidence': extraction.classification_confidence,
        'matched_signals': extraction.matched_signals,
        'classifier_version': extraction.classifier_version,
        'message': extraction.message,
        'error_message': extraction.error_message,
        'processing_time_ms': extraction.processing_time_ms,
        'created_at': extraction.created_at,
        'updated_at': extraction.updated_at,
    }


def _history_payload(extraction: Extraction) -> dict[str, object]:
    payload = _serialize_extraction(extraction)
    return {
        'id': extraction.id,
        'status': payload['status'],
        'original_filename': payload['filename'],
        'content_type': payload['content_type'],
        'file_size': payload['file_size'],
        'image_url': payload['image_url'],
        'storage_provider': payload['storage_provider'],
        'classification_label': payload['classification_label'],
        'classification_score': payload['classification_score'],
        'classification_confidence': payload['classification_confidence'],
        'message': payload['message'],
        'error_message': payload['error_message'],
        'processing_time_ms': payload['processing_time_ms'],
        'created_at': payload['created_at'],
        'updated_at': payload['updated_at'],
    }
