from uuid import uuid4

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DummyUploadResponseSerializer, ImageUploadSerializer


class ExtractionUploadView(APIView):
    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = serializer.validated_data['image']
        payload = {
            'id': str(uuid4()),
            'status': 'received',
            'filename': image.name,
            'content_type': image.content_type,
            'message': 'Image received successfully. Dummy processing response returned.',
        }
        response_serializer = DummyUploadResponseSerializer(payload)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
