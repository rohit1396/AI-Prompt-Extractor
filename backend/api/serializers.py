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
    image_url = serializers.CharField(allow_blank=True, required=False)
    storage_provider = serializers.CharField(required=False)
    cloudinary_public_id = serializers.CharField(allow_blank=True, required=False)
    extracted_text = serializers.CharField()
    is_prompt = serializers.BooleanField(required=False)
    prompt_confidence = serializers.IntegerField(allow_null=True, required=False)
    raw_ocr_text = serializers.CharField(required=False)
    classification_label = serializers.CharField(allow_blank=True, required=False)
    classification_score = serializers.IntegerField(allow_null=True, required=False)
    classification_confidence = serializers.IntegerField(allow_null=True, required=False)
    matched_signals = serializers.JSONField(required=False)
    classifier_version = serializers.CharField(allow_blank=True, required=False)
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
            'storage_provider',
            'cloudinary_public_id',
            'cloudinary_secure_url',
            'extracted_text',
            'is_prompt',
            'prompt_confidence',
            'raw_ocr_text',
            'classification_label',
            'classification_score',
            'classification_confidence',
            'matched_signals',
            'classifier_version',
            'message',
            'error_message',
            'processing_time_ms',
            'created_at',
            'updated_at',
        )
