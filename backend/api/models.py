import uuid

from django.contrib.auth.models import User
from django.db import models


class GoogleIdentity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_identity')
    google_sub = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.email or self.google_sub


class Extraction(models.Model):
    class StorageProvider(models.TextChoices):
        LOCAL = 'local', 'Local'
        CLOUDINARY = 'cloudinary', 'Cloudinary'

    class ClassificationLabel(models.TextChoices):
        PROMPT = 'prompt', 'Prompt'
        NOT_PROMPT = 'not_prompt', 'Not prompt'
        UNCERTAIN = 'uncertain', 'Uncertain'

    class Status(models.TextChoices):
        RECEIVED = 'received', 'Received'
        QUEUED = 'queued', 'Queued'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='extractions',
    )
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
    raw_ocr_text = models.TextField(blank=True, default='')
    optimized_prompt = models.TextField(blank=True, default='')
    optimizer_template = models.CharField(max_length=30, blank=True, default='')
    optimizer_components = models.JSONField(default=dict, blank=True)
    optimizer_version = models.CharField(max_length=30, blank=True, default='')
    classification_label = models.CharField(
        max_length=20,
        choices=ClassificationLabel.choices,
        blank=True,
        default='',
    )
    classification_score = models.IntegerField(null=True, blank=True)
    classification_confidence = models.PositiveSmallIntegerField(null=True, blank=True)
    matched_signals = models.JSONField(default=list, blank=True)
    classifier_version = models.CharField(max_length=20, blank=True, default='')
    message = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.original_filename} ({self.status})'
