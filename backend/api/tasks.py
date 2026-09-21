from __future__ import annotations

import logging
import os
from time import perf_counter

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .classification import classify_prompt_text, normalize_text
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
    raw_ocr_text: str | None = None,
    classification_label: str | None = None,
    classification_score: int | None = None,
    classification_confidence: int | None = None,
    matched_signals: list[dict[str, object]] | None = None,
    classifier_version: str | None = None,
    processing_time_ms: int | None = None,
) -> None:
    if message is not None:
        extraction.message = message
    if error_message is not None:
        extraction.error_message = error_message
    if extracted_text is not None:
        extraction.extracted_text = extracted_text
    if raw_ocr_text is not None:
        extraction.raw_ocr_text = raw_ocr_text
    if classification_label is not None:
        extraction.classification_label = classification_label
    if classification_score is not None:
        extraction.classification_score = classification_score
    if classification_confidence is not None:
        extraction.classification_confidence = classification_confidence
    if matched_signals is not None:
        extraction.matched_signals = matched_signals
    if classifier_version is not None:
        extraction.classifier_version = classifier_version
    if processing_time_ms is not None:
        extraction.processing_time_ms = processing_time_ms

    extraction.status = status
    extraction.save(
        update_fields=[
            'status',
            'message',
            'error_message',
            'extracted_text',
            'raw_ocr_text',
            'classification_label',
            'classification_score',
            'classification_confidence',
            'matched_signals',
            'classifier_version',
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
        normalized_text = normalize_text(extracted_text)
        classification = classify_prompt_text(normalized_text)
        # OCR is useful even when the classifier is unsure; classification is an
        # assessment of the text, not a reason to discard it.
        result_text = extracted_text
        message = {
            'prompt': 'Prompt-like text extracted successfully.',
            'not_prompt': 'OCR completed, but the image does not look like a prompt.',
            'uncertain': 'OCR completed, but prompt evidence is limited.',
        }[classification.label]
        processing_time_ms = int((perf_counter() - started_at) * 1000)

        with transaction.atomic():
            extraction = Extraction.objects.select_for_update().get(pk=extraction_id)
            if extraction.status != Extraction.Status.PROCESSING:
                return extraction.status
            _set_extraction_status(
                extraction,
                status=Extraction.Status.COMPLETED,
                message=message,
                error_message='',
                extracted_text=result_text,
                raw_ocr_text=extracted_text,
                classification_label=classification.label,
                classification_score=classification.score,
                classification_confidence=classification.confidence,
                matched_signals=[
                    {
                        'text': signal.text,
                        'category': signal.category,
                        'weight': signal.weight,
                        'polarity': signal.polarity,
                    }
                    for signal in classification.matched_signals
                ],
                classifier_version=classification.classifier_version,
                processing_time_ms=processing_time_ms,
            )

        logger.info(
            'Extraction completed extraction_id=%s processing_time_ms=%s text_length=%s classification=%s score=%s confidence=%s',
            extraction_id,
            processing_time_ms,
            len(extracted_text),
            classification.label,
            classification.score,
            classification.confidence,
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
