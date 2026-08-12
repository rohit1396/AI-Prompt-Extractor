from rest_framework import serializers

from .models import Extraction


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def validate_image(self, value):
        max_size = 10 * 1024 * 1024
        allowed_types = {'image/png', 'image/jpeg', 'image/webp'}

        if value.size > max_size:
            raise serializers.ValidationError('Image must be 10MB or smaller.')

        if value.content_type not in allowed_types:
            raise serializers.ValidationError('Unsupported image type.')

        return value


class ExtractionResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    filename = serializers.CharField()
    content_type = serializers.CharField()
    file_size = serializers.IntegerField()
    extracted_text = serializers.CharField()
    message = serializers.CharField()
    error_message = serializers.CharField(allow_blank=True, required=False)
    processing_time_ms = serializers.IntegerField(allow_null=True, required=False)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)


class ExtractionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extraction
        fields = (
            'id',
            'status',
            'original_filename',
            'content_type',
            'file_size',
            'extracted_text',
            'message',
            'error_message',
            'processing_time_ms',
            'created_at',
            'updated_at',
        )
