from __future__ import annotations

import logging
import os
from time import perf_counter

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .cloudinary import download_remote_file
from .models import Extraction
from .ocr import extract_prompt_text_from_path

logger = logging.getLogger(__name__)


def _set_extraction_status(
    extraction: Extraction,
    *,
    status: str,
    message: str | None = None,
    error_message: str | None = None,
    extracted_text: str | None = None,
    processing_time_ms: int | None = None,
) -> None:
    if message is not None:
        extraction.message = message
    if error_message is not None:
        extraction.error_message = error_message
    if extracted_text is not None:
        extraction.extracted_text = extracted_text
    if processing_time_ms is not None:
        extraction.processing_time_ms = processing_time_ms

    extraction.status = status
    extraction.save(
        update_fields=[
            'status',
            'message',
            'error_message',
            'extracted_text',
            'processing_time_ms',
            'updated_at',
        ],
    )


def _resolve_source_path(extraction: Extraction) -> tuple[str, list[str]]:
    temp_paths: list[str] = []

    if extraction.storage_provider == Extraction.StorageProvider.CLOUDINARY:
        remote_url = extraction.cloudinary_secure_url
        if not remote_url:
            raise FileNotFoundError(f'Cloudinary URL missing for extraction {extraction.id}')
        temp_path = download_remote_file(remote_url)
        temp_paths.append(temp_path)
        return temp_path, temp_paths

    if extraction.image:
        try:
            source_path = extraction.image.path
            if source_path:
                return source_path, temp_paths
        except (ValueError, OSError, NotImplementedError):
            pass

    if extraction.cloudinary_secure_url:
        temp_path = download_remote_file(extraction.cloudinary_secure_url)
        temp_paths.append(temp_path)
        return temp_path, temp_paths

    raise FileNotFoundError(f'Image file does not exist for extraction {extraction.id}')


def process_extraction_job(extraction_id: str) -> str:
    started_at = perf_counter()

    try:
        with transaction.atomic():
            extraction = Extraction.objects.select_for_update().get(pk=extraction_id)
            if extraction.status in {Extraction.Status.COMPLETED, Extraction.Status.FAILED}:
                logger.info(
                    'Skipping extraction_id=%s because it is already %s',
                    extraction_id,
                    extraction.status,
                )
                return extraction.status

            if extraction.status != Extraction.Status.QUEUED:
                logger.info(
                    'Skipping extraction_id=%s because it is in status=%s',
                    extraction_id,
                    extraction.status,
                )
                return extraction.status

            _set_extraction_status(
                extraction,
                status=Extraction.Status.PROCESSING,
                message='OCR processing started.',
                error_message='',
            )
    except ObjectDoesNotExist:
        logger.warning('Skipping extraction_id=%s because the record no longer exists', extraction_id)
        return 'missing'

    try:
        source_path, temp_paths = _resolve_source_path(extraction)
        try:
            extracted_text = extract_prompt_text_from_path(
                source_path,
                extraction_id=str(extraction.id),
            )
        finally:
            for temp_path in temp_paths:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except OSError:
                    pass
        processing_time_ms = int((perf_counter() - started_at) * 1000)

        with transaction.atomic():
            extraction = Extraction.objects.select_for_update().get(pk=extraction_id)
            if extraction.status != Extraction.Status.PROCESSING:
                return extraction.status
            _set_extraction_status(
                extraction,
                status=Extraction.Status.COMPLETED,
                message='Prompt text extracted successfully.',
                error_message='',
                extracted_text=extracted_text,
                processing_time_ms=processing_time_ms,
            )

        logger.info(
            'Extraction completed extraction_id=%s processing_time_ms=%s text_length=%s',
            extraction_id,
            processing_time_ms,
            len(extracted_text),
        )
        return Extraction.Status.COMPLETED
    except Exception as exc:
        processing_time_ms = int((perf_counter() - started_at) * 1000)
        error_message = str(exc) or 'OCR processing failed.'

        with transaction.atomic():
            extraction = Extraction.objects.select_for_update().get(pk=extraction_id)
            if extraction.status != Extraction.Status.PROCESSING:
                return extraction.status
            _set_extraction_status(
                extraction,
                status=Extraction.Status.FAILED,
                message='Unable to extract text from the uploaded image.',
                error_message=error_message,
                extracted_text='',
                processing_time_ms=processing_time_ms,
            )

        logger.exception('Extraction failed extraction_id=%s', extraction_id)
        return Extraction.Status.FAILED


@shared_task(name='api.process_extraction')
def process_extraction(extraction_id: str) -> str:
    return process_extraction_job(extraction_id)
