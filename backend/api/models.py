import uuid

from django.db import models


class Extraction(models.Model):
    class StorageProvider(models.TextChoices):
        LOCAL = 'local', 'Local'
        CLOUDINARY = 'cloudinary', 'Cloudinary'

    class Status(models.TextChoices):
        RECEIVED = 'received', 'Received'
        QUEUED = 'queued', 'Queued'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='extractions/%Y/%m/%d/', null=True, blank=True)
    storage_provider = models.CharField(
        max_length=20,
        choices=StorageProvider.choices,
        default=StorageProvider.LOCAL,
    )
    cloudinary_public_id = models.CharField(max_length=255, blank=True, default='')
    cloudinary_secure_url = models.URLField(blank=True, default='')
    cloudinary_version = models.PositiveIntegerField(null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField()
    content_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    extracted_text = models.TextField(blank=True, default='')
    message = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.original_filename} ({self.status})'
