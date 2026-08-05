from uuid import uuid4

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .ocr import extract_prompt_text
from .serializers import ExtractionResponseSerializer, ImageUploadSerializer

logger = logging.getLogger(__name__)


class ExtractionUploadView(APIView):
    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = serializer.validated_data['image']
        try:
            extracted_text = extract_prompt_text(image)
        except Exception:
            logger.exception('Prompt extraction failed for %s', image.name)
            payload = {
                'id': str(uuid4()),
                'status': 'failed',
                'filename': image.name,
                'content_type': image.content_type,
                'extracted_text': '',
                'message': 'Unable to extract text from the uploaded image.',
            }
            response_serializer = ExtractionResponseSerializer(payload)
            return Response(response_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        message = 'Prompt text extracted successfully.'
        if not extracted_text.strip():
            message = 'No readable prompt text was detected in the uploaded image.'

        payload = {
            'id': str(uuid4()),
            'status': 'completed',
            'filename': image.name,
            'content_type': image.content_type,
            'extracted_text': extracted_text,
            'message': message,
        }
        response_serializer = ExtractionResponseSerializer(payload)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
