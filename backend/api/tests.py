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

from .classification import classify_prompt_text
from .models import Extraction
from .tasks import process_extraction_job


def _build_image_file(filename: str = 'prompt.png', *, color: str = 'white') -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new('RGB', (128, 128), color=color).save(buffer, format='PNG')
    buffer.seek(0)
    return SimpleUploadedFile(filename, buffer.read(), content_type='image/png')


def _build_temp_image_path(*, color: str = 'white') -> str:
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_file.close()
    Image.new('RGB', (128, 128), color=color).save(temp_file.name, format='PNG')
    return temp_file.name


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
        with override_settings(USE_CLOUDINARY_STORAGE=False):
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

    def test_upload_to_cloudinary_persists_remote_metadata(self):
        with override_settings(
            USE_CLOUDINARY_STORAGE=True,
            CLOUDINARY_CLOUD_NAME='demo',
            CLOUDINARY_API_KEY='key',
            CLOUDINARY_API_SECRET='secret',
        ):
            with patch('api.views.upload_image_to_cloudinary') as mock_upload:
                mock_upload.return_value = type(
                    'CloudinaryUploadResult',
                    (),
                    {
                        'public_id': 'promptlens/extractions/demo-public-id',
                        'secure_url': 'https://res.cloudinary.com/demo/image/upload/v1/promptlens/extractions/demo-public-id.png',
                        'version': 1,
                    },
                )()

                with patch('api.tasks.process_extraction.delay') as mock_delay:
                    with self.captureOnCommitCallbacks(execute=True):
                        response = self.client.post(
                            '/api/v1/extractions/',
                            {'image': _build_image_file()},
                            format='multipart',
                        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['storage_provider'], 'cloudinary')
        self.assertEqual(response.data['cloudinary_public_id'], 'promptlens/extractions/demo-public-id')
        self.assertEqual(
            response.data['image_url'],
            'https://res.cloudinary.com/demo/image/upload/v1/promptlens/extractions/demo-public-id.png',
        )

        extraction = Extraction.objects.get()
        self.assertEqual(extraction.storage_provider, Extraction.StorageProvider.CLOUDINARY)
        self.assertEqual(extraction.cloudinary_public_id, 'promptlens/extractions/demo-public-id')
        self.assertEqual(extraction.cloudinary_secure_url, response.data['image_url'])
        mock_upload.assert_called_once()
        mock_delay.assert_called_once_with(str(extraction.id))

    def test_cloudinary_upload_failure_returns_service_unavailable(self):
        with override_settings(
            USE_CLOUDINARY_STORAGE=True,
            CLOUDINARY_CLOUD_NAME='demo',
            CLOUDINARY_API_KEY='key',
            CLOUDINARY_API_SECRET='secret',
        ):
            with patch('api.views.upload_image_to_cloudinary', side_effect=RuntimeError('Cloudinary down')):
                response = self.client.post(
                    '/api/v1/extractions/',
                    {'image': _build_image_file()},
                    format='multipart',
                )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data['detail'], 'Cloudinary down')
        self.assertEqual(Extraction.objects.count(), 0)

    def test_db_failure_after_cloudinary_upload_cleans_up_asset(self):
        with override_settings(
            USE_CLOUDINARY_STORAGE=True,
            CLOUDINARY_CLOUD_NAME='demo',
            CLOUDINARY_API_KEY='key',
            CLOUDINARY_API_SECRET='secret',
        ):
            with patch('api.views.upload_image_to_cloudinary') as mock_upload:
                mock_upload.return_value = type(
                    'CloudinaryUploadResult',
                    (),
                    {
                        'public_id': 'promptlens/extractions/failure-case',
                        'secure_url': 'https://res.cloudinary.com/demo/image/upload/v1/promptlens/extractions/failure-case.png',
                        'version': 1,
                    },
                )()
                with patch('api.views.Extraction.objects.create', side_effect=RuntimeError('db unavailable')):
                    with patch('api.views.delete_image_from_cloudinary') as mock_delete:
                        response = self.client.post(
                            '/api/v1/extractions/',
                            {'image': _build_image_file()},
                            format='multipart',
                        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data['detail'], 'Unable to persist the uploaded image.')
        mock_delete.assert_called_once_with('promptlens/extractions/failure-case')

    def test_worker_transitions_queued_extraction_to_completed(self):
        extraction = self._create_queued_extraction()

        with patch('api.tasks.extract_prompt_text_from_path', return_value='Create a cinematic portrait'):
            status = process_extraction_job(str(extraction.id))

        extraction.refresh_from_db()
        self.assertEqual(status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.extracted_text, 'Create a cinematic portrait')
        self.assertEqual(extraction.raw_ocr_text, 'Create a cinematic portrait')
        self.assertEqual(extraction.classification_label, 'uncertain')
        self.assertEqual(extraction.classification_score, 7)
        self.assertEqual(extraction.classification_confidence, 23)
        self.assertEqual(extraction.message, 'OCR completed, but prompt evidence is limited.')
        self.assertIsNotNone(extraction.processing_time_ms)
        self.assertEqual(extraction.error_message, '')

    def test_worker_preserves_non_prompt_ocr_results(self):
        extraction = self._create_queued_extraction()

        with patch('api.tasks.extract_prompt_text_from_path', return_value='Follow me for more AI images'):
            status = process_extraction_job(str(extraction.id))

        extraction.refresh_from_db()
        self.assertEqual(status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.extracted_text, 'Follow me for more AI images')
        self.assertEqual(extraction.raw_ocr_text, 'Follow me for more AI images')
        self.assertEqual(extraction.classification_label, 'not_prompt')
        self.assertFalse(extraction.classification_label == 'prompt')
        self.assertEqual(extraction.classification_confidence, 0)
        self.assertEqual(extraction.message, 'OCR completed, but the image does not look like a prompt.')
        self.assertGreater(len(extraction.matched_signals), 0)

    def test_worker_downloads_cloudinary_asset_before_ocr(self):
        temp_path = _build_temp_image_path()
        extraction = Extraction.objects.create(
            image=None,
            storage_provider=Extraction.StorageProvider.CLOUDINARY,
            cloudinary_public_id='promptlens/extractions/cloudinary-case',
            cloudinary_secure_url='https://res.cloudinary.com/demo/image/upload/v1/promptlens/extractions/cloudinary-case.png',
            original_filename='prompt.png',
            file_size=123,
            content_type='image/png',
            status=Extraction.Status.QUEUED,
            message='Image received. OCR job queued.',
        )

        try:
            with patch('api.tasks.download_remote_file', return_value=temp_path) as mock_download:
                with patch('api.tasks.extract_prompt_text_from_path', return_value='Cloudinary prompt text'):
                    status = process_extraction_job(str(extraction.id))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        extraction.refresh_from_db()
        self.assertEqual(status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.extracted_text, 'Cloudinary prompt text')
        self.assertEqual(extraction.classification_label, 'uncertain')
        mock_download.assert_called_once_with(extraction.cloudinary_secure_url)

    def test_detail_endpoint_includes_classification_fields(self):
        extraction = self._create_queued_extraction()

        with patch('api.tasks.extract_prompt_text_from_path', return_value='cinematic portrait, 35mm lens'):
            process_extraction_job(str(extraction.id))

        response = self.client.get(f'/api/v1/extractions/{extraction.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_prompt'])
        self.assertEqual(response.data['classification_label'], 'prompt')
        self.assertGreater(response.data['prompt_confidence'], 0)
        self.assertEqual(response.data['raw_ocr_text'], 'cinematic portrait, 35mm lens')
        self.assertGreater(len(response.data['matched_signals']), 0)

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


class PromptClassificationTests(SimpleTestCase):
    def test_classifier_scores_prompt_like_text(self):
        result = classify_prompt_text('cinematic portrait, 35mm lens, shallow depth of field')

        self.assertTrue(result.is_prompt)
        self.assertEqual(result.label, 'prompt')
        self.assertGreaterEqual(result.score, 5)
        self.assertGreater(result.confidence, 0)
        self.assertLess(result.confidence, 70)
        self.assertTrue(result.matched_signals)

    def test_classifier_rejects_social_media_text(self):
        result = classify_prompt_text('Follow me for more AI images')

        self.assertFalse(result.is_prompt)
        self.assertEqual(result.label, 'not_prompt')
        self.assertLessEqual(result.score, 0)
        self.assertEqual(result.confidence, 0)

    def test_classifier_normalizes_input_before_matching(self):
        result = classify_prompt_text('CINEMATIC   PORTRAIT')

        self.assertEqual(result.label, 'uncertain')

    def test_classifier_accepts_explicit_ocr_aliases(self):
        result = classify_prompt_text('Cinematic closeup, volumetric lightning, highy detailed')

        self.assertEqual(result.label, 'prompt')
        self.assertEqual({signal.text for signal in result.matched_signals}, {'cinematic', 'close-up', 'volumetric lighting', 'highly detailed'})

    def test_classifier_treats_syntax_with_punctuation_as_strong_evidence(self):
        result = classify_prompt_text('portrait of a fox --ar 16:9 --stylize 250')

        self.assertEqual(result.label, 'prompt')
        self.assertGreaterEqual(result.confidence, 50)

    def test_classifier_caps_repeated_category_keywords(self):
        result = classify_prompt_text('cinematic digital art concept art illustration anime character design')

        self.assertEqual(result.label, 'uncertain')
        self.assertEqual(result.score, 8)
        self.assertEqual(result.confidence, 27)

    def test_classifier_rejects_negative_text_even_with_generic_prompt_terms(self):
        result = classify_prompt_text('Cinematic portrait. Follow me, subscribe, and visit our website.')

        self.assertEqual(result.label, 'not_prompt')
        self.assertEqual(result.confidence, 0)

    def test_classifier_handles_empty_ocr_text(self):
        result = classify_prompt_text('')

        self.assertEqual(result.label, 'uncertain')
        self.assertEqual(result.confidence, 0)
        self.assertFalse(result.matched_signals)


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
