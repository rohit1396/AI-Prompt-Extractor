from rest_framework import serializers


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


class DummyUploadResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    filename = serializers.CharField()
    content_type = serializers.CharField()
    message = serializers.CharField()
