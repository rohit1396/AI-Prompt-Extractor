from __future__ import annotations

import os
import subprocess
import shutil
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from PIL import Image
from rest_framework.test import APITestCase

from .models import Extraction
from .tasks import process_extraction_job


def _build_image_file(filename: str = 'prompt.png', *, color: str = 'white') -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new('RGB', (128, 128), color=color).save(buffer, format='PNG')
    buffer.seek(0)
    return SimpleUploadedFile(filename, buffer.read(), content_type='image/png')


class ExtractionAsyncWorkflowTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp(prefix='promptlens-media-')
        cls._media_override = override_settings(MEDIA_ROOT=Path(cls._media_root))
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    def _create_queued_extraction(self) -> Extraction:
        image = _build_image_file()
        return Extraction.objects.create(
            image=image,
            original_filename='prompt.png',
            file_size=image.size,
            content_type='image/png',
            status=Extraction.Status.QUEUED,
            message='Image received. OCR job queued.',
        )

    def test_upload_marks_extraction_queued_and_enqueues_job(self):
        with patch('api.tasks.process_extraction.delay') as mock_delay:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    '/api/v1/extractions/',
                    {'image': _build_image_file()},
                    format='multipart',
                )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'queued')
        self.assertEqual(Extraction.objects.count(), 1)

        extraction = Extraction.objects.get()
        self.assertEqual(extraction.status, Extraction.Status.QUEUED)
        self.assertEqual(extraction.message, 'Image received. OCR job queued.')
        mock_delay.assert_called_once_with(str(extraction.id))

    def test_worker_transitions_queued_extraction_to_completed(self):
        extraction = self._create_queued_extraction()

        with patch('api.tasks.extract_prompt_text_from_path', return_value='Create a cinematic portrait'):
            status = process_extraction_job(str(extraction.id))

        extraction.refresh_from_db()
        self.assertEqual(status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.extracted_text, 'Create a cinematic portrait')
        self.assertEqual(extraction.message, 'Prompt text extracted successfully.')
        self.assertIsNotNone(extraction.processing_time_ms)
        self.assertEqual(extraction.error_message, '')

    def test_worker_marks_extraction_failed_on_ocr_error(self):
        extraction = self._create_queued_extraction()

        with patch('api.tasks.extract_prompt_text_from_path', side_effect=RuntimeError('OCR unavailable')):
            status = process_extraction_job(str(extraction.id))

        extraction.refresh_from_db()
        self.assertEqual(status, Extraction.Status.FAILED)
        self.assertEqual(extraction.status, Extraction.Status.FAILED)
        self.assertEqual(extraction.extracted_text, '')
        self.assertIn('OCR unavailable', extraction.error_message)
        self.assertEqual(extraction.message, 'Unable to extract text from the uploaded image.')

    def test_worker_skips_already_completed_extractions(self):
        image = _build_image_file()
        extraction = Extraction.objects.create(
            image=image,
            original_filename='prompt.png',
            file_size=image.size,
            content_type='image/png',
            status=Extraction.Status.COMPLETED,
            extracted_text='Ready text',
            message='Prompt text extracted successfully.',
            processing_time_ms=1234,
        )

        with patch('api.tasks.extract_prompt_text_from_path') as mock_extract:
            status = process_extraction_job(str(extraction.id))

        extraction.refresh_from_db()
        self.assertEqual(status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.extracted_text, 'Ready text')
        mock_extract.assert_not_called()

    def test_worker_handles_missing_extraction_gracefully(self):
        status = process_extraction_job('11111111-1111-1111-1111-111111111111')

        self.assertEqual(status, 'missing')


class SettingsEnvLoadingTests(SimpleTestCase):
    def test_settings_loads_root_env_without_manual_export(self):
        backend_dir = Path(__file__).resolve().parents[1]
        script = (
            "from config import settings; "
            "print(settings.DEBUG); "
            "print(settings.DATABASES['default']['NAME'])"
        )
        env = {
            'PYTHONPATH': str(backend_dir),
            'PATH': os.environ.get('PATH', ''),
        }

        result = subprocess.run(
            [sys.executable, '-c', script],
            cwd=backend_dir,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn('True', result.stdout)
        self.assertIn('promptlens', result.stdout)
