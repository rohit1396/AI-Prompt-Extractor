from django.contrib import admin

from .models import Extraction, GoogleIdentity


@admin.register(GoogleIdentity)
class GoogleIdentityAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'google_sub', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'email', 'google_sub')


@admin.register(Extraction)
class ExtractionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'original_filename',
        'status',
        'classification_label',
        'classification_confidence',
        'storage_provider',
        'file_size',
        'content_type',
        'processing_time_ms',
        'created_at',
    )
    list_filter = ('status', 'classification_label', 'storage_provider', 'content_type', 'created_at')
    search_fields = ('id', 'original_filename', 'extracted_text', 'raw_ocr_text', 'message', 'error_message')
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'processing_time_ms',
        'file_size',
        'content_type',
        'original_filename',
        'storage_provider',
        'cloudinary_public_id',
        'cloudinary_secure_url',
        'cloudinary_version',
        'raw_ocr_text',
        'classification_label',
        'classification_score',
        'classification_confidence',
        'matched_signals',
        'classifier_version',
    )
