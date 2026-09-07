from django.contrib import admin

from .models import Extraction


@admin.register(Extraction)
class ExtractionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'original_filename',
        'status',
        'storage_provider',
        'file_size',
        'content_type',
        'processing_time_ms',
        'created_at',
    )
    list_filter = ('status', 'storage_provider', 'content_type', 'created_at')
    search_fields = ('id', 'original_filename', 'extracted_text', 'message', 'error_message')
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
    )
