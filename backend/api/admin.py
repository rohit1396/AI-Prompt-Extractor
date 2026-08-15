from django.contrib import admin

from .models import Extraction


@admin.register(Extraction)
class ExtractionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'original_filename',
        'status',
        'file_size',
        'content_type',
        'processing_time_ms',
        'created_at',
    )
    list_filter = ('status', 'content_type', 'created_at')
    search_fields = ('id', 'original_filename', 'extracted_text', 'message', 'error_message')
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'processing_time_ms',
        'file_size',
        'content_type',
        'original_filename',
    )
