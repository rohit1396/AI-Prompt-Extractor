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

        started_at = time.perf_counter()
        try:
            extracted_text = extract_prompt_text(extraction.image)
        except Exception as exc:
            logger.exception('Prompt extraction failed for %s', image.name)
            extraction.status = Extraction.Status.FAILED
            extraction.extracted_text = ''
            extraction.message = 'Unable to extract text from the uploaded image.'
            extraction.error_message = str(exc)
            extraction.processing_time_ms = int((time.perf_counter() - started_at) * 1000)
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
            return Response(response_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        message = 'Prompt text extracted successfully.'
        if not extracted_text.strip():
            message = 'No readable prompt text was detected in the uploaded image.'

        extraction.status = Extraction.Status.COMPLETED
        extraction.extracted_text = extracted_text
        extraction.message = message
        extraction.error_message = ''
        extraction.processing_time_ms = int((time.perf_counter() - started_at) * 1000)
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
