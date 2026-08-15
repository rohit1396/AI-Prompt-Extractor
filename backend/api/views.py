import logging
import time

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .ocr import extract_prompt_text
from .models import Extraction
from .serializers import ExtractionResponseSerializer, ImageUploadSerializer

logger = logging.getLogger(__name__)


class ExtractionUploadView(APIView):
    def post(self, request):
        request_started_at = time.perf_counter()
        logger.info(
            'STEP 1: request received method=%s path=%s content_type=%s',
            request.method,
            request.path,
            request.content_type,
        )

        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = serializer.validated_data['image']
        extraction = Extraction.objects.create(
            image=image,
            original_filename=image.name,
            file_size=image.size,
            content_type=image.content_type,
            status=Extraction.Status.PROCESSING,
        )
        logger.info(
            'STEP 2: image saved extraction_id=%s filename=%s file_size=%s elapsed_ms=%s',
            extraction.id,
            image.name,
            image.size,
            int((time.perf_counter() - request_started_at) * 1000),
        )

        started_at = time.perf_counter()
        try:
            logger.info(
                'STEP 3: starting OCR extraction_id=%s elapsed_ms=%s',
                extraction.id,
                int((time.perf_counter() - request_started_at) * 1000),
            )
            extracted_text = extract_prompt_text(extraction.image, extraction_id=str(extraction.id))
            logger.info(
                'STEP 4: OCR completed extraction_id=%s extracted_chars=%s elapsed_ms=%s',
                extraction.id,
                len(extracted_text),
                int((time.perf_counter() - request_started_at) * 1000),
            )
        except Exception as exc:
            logger.exception(
                'Prompt extraction failed extraction_id=%s filename=%s elapsed_ms=%s',
                extraction.id,
                image.name,
                int((time.perf_counter() - request_started_at) * 1000),
            )
            extraction.status = Extraction.Status.FAILED
            extraction.extracted_text = ''
            extraction.message = 'Unable to extract text from the uploaded image.'
            extraction.error_message = str(exc)
            extraction.processing_time_ms = int((time.perf_counter() - started_at) * 1000)
            logger.info(
                'STEP 5: saving extraction extraction_id=%s status=%s elapsed_ms=%s',
                extraction.id,
                extraction.status,
                int((time.perf_counter() - request_started_at) * 1000),
            )
            extraction.save(
                update_fields=[
                    'status',
                    'extracted_text',
                    'message',
                    'error_message',
                    'processing_time_ms',
                    'updated_at',
                ],
            )
            payload = _serialize_extraction(extraction)
            response_serializer = ExtractionResponseSerializer(payload)
            logger.info(
                'STEP 6: response ready extraction_id=%s status_code=%s elapsed_ms=%s',
                extraction.id,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                int((time.perf_counter() - request_started_at) * 1000),
            )
            return Response(response_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        message = 'Prompt text extracted successfully.'
        if not extracted_text.strip():
            message = 'No readable prompt text was detected in the uploaded image.'

        extraction.status = Extraction.Status.COMPLETED
        extraction.extracted_text = extracted_text
        extraction.message = message
        extraction.error_message = ''
        extraction.processing_time_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            'STEP 5: saving extraction extraction_id=%s status=%s elapsed_ms=%s',
            extraction.id,
            extraction.status,
            int((time.perf_counter() - request_started_at) * 1000),
        )
        extraction.save(
            update_fields=[
                'status',
                'extracted_text',
                'message',
                'error_message',
                'processing_time_ms',
                'updated_at',
            ],
        )

        payload = _serialize_extraction(extraction)
        response_serializer = ExtractionResponseSerializer(payload)
        logger.info(
            'STEP 6: response ready extraction_id=%s status_code=%s elapsed_ms=%s',
            extraction.id,
            status.HTTP_201_CREATED,
            int((time.perf_counter() - request_started_at) * 1000),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


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
