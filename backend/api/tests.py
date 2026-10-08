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
from django.contrib.auth.models import User
from django.test import SimpleTestCase, override_settings
from django.core.management import call_command
from PIL import Image
from rest_framework.test import APITestCase

from .classification import classify_prompt_text
from .models import Extraction
from .ocr import OCRTextLine, _normalize_ocr_result, _select_prompt_lines
from .optimizer import optimize_prompt
from .observability import capture_exception
from config.sentry import before_send
from .tasks import process_extraction_job
from .text_cleaning import clean_extracted_text


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

    def setUp(self):
        self.user = User.objects.create_user(username='test-user', email='test@example.com')
        self.client.force_authenticate(self.user)

    def test_extraction_endpoints_require_authentication(self):
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get('/api/v1/extractions/history/').status_code, (401, 403))
        self.assertIn(
            self.client.post('/api/v1/extractions/', {'image': _build_image_file()}, format='multipart').status_code,
            (401, 403),
        )

    def test_history_is_scoped_to_authenticated_user(self):
        own = self._create_queued_extraction()
        other = User.objects.create_user(username='other-user', email='other@example.com')
        image = _build_image_file(filename='other.png')
        Extraction.objects.create(
            user=other,
            image=image,
            original_filename='other.png',
            file_size=image.size,
            content_type='image/png',
            status=Extraction.Status.QUEUED,
            message='Status recorded.',
        )
        response = self.client.get('/api/v1/extractions/history/')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(own.id))

    def _create_queued_extraction(self) -> Extraction:
        image = _build_image_file()
        return Extraction.objects.create(
            user=self.user,
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
        self.assertEqual(extraction.optimizer_template, 'portrait')
        self.assertIn('cinematic portrait', extraction.optimized_prompt)
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
        self.assertEqual(extraction.optimized_prompt, '')
        self.assertEqual(extraction.optimizer_components, {})
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
        self.assertIn('optimized_prompt', response.data)
        self.assertEqual(response.data['optimizer_template'], 'portrait')
        self.assertGreater(len(response.data['matched_signals']), 0)

    def test_detail_endpoint_returns_not_found_for_unknown_extraction(self):
        response = self.client.get('/api/v1/extractions/11111111-1111-1111-1111-111111111111/')

        self.assertEqual(response.status_code, 404)

    def test_history_endpoint_returns_newest_first_summary_records(self):
        older = self._create_queued_extraction()
        newer = self._create_queued_extraction()
        Extraction.objects.filter(pk=older.pk).update(original_filename='older.png')
        Extraction.objects.filter(pk=newer.pk).update(
            original_filename='newer.png',
            status=Extraction.Status.COMPLETED,
            classification_label=Extraction.ClassificationLabel.PROMPT,
            extracted_text='A cinematic portrait of a traveler in a rain-soaked neon city, dramatic lighting, highly detailed, 35mm lens, atmospheric depth',
        )

        response = self.client.get('/api/v1/extractions/history/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual([item['filename'] for item in response.data['results']], ['newer.png', 'older.png'])
        self.assertNotIn('extracted_text', response.data['results'][0])
        self.assertIn('classification_score', response.data['results'][0])
        self.assertEqual(
            response.data['results'][0]['prompt_preview'],
            'A cinematic portrait of a traveler in a rain-soaked neon city, dramatic li…',
        )
        self.assertTrue(response.data['results'][0]['image_url'].startswith('http://testserver/media/'))
        self.assertEqual(response.data['results'][1]['prompt_preview'], '')

    def test_history_endpoint_paginates_and_includes_all_statuses(self):
        for index, extraction_status in enumerate(
            [Extraction.Status.RECEIVED, Extraction.Status.QUEUED, Extraction.Status.PROCESSING]
        ):
            image = _build_image_file(filename=f'{index}.png')
            Extraction.objects.create(
                user=self.user,
                image=image,
                original_filename=f'{index}.png',
                file_size=image.size,
                content_type='image/png',
                status=extraction_status,
                message='Status recorded.',
            )

        response = self.client.get('/api/v1/extractions/history/?page_size=2&page=2')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['previous'])
        self.assertIsNone(response.data['next'])

    def test_worker_marks_extraction_failed_on_ocr_error(self):
        extraction = self._create_queued_extraction()

        with patch('api.tasks.capture_exception') as mock_capture:
            with patch('api.tasks.extract_prompt_text_from_path', side_effect=RuntimeError('OCR unavailable')):
                status = process_extraction_job(str(extraction.id))

        mock_capture.assert_called_once()
        self.assertEqual(mock_capture.call_args.kwargs['operation'], 'extraction_processing')
        self.assertEqual(mock_capture.call_args.kwargs['extraction'], extraction)

        extraction.refresh_from_db()
        self.assertEqual(status, Extraction.Status.FAILED)
        self.assertEqual(extraction.status, Extraction.Status.FAILED)
        self.assertEqual(extraction.extracted_text, '')
        self.assertIn('OCR unavailable', extraction.error_message)
        self.assertEqual(extraction.message, 'Unable to extract text from the uploaded image.')

    def test_sentry_scrubber_removes_sensitive_request_data(self):
        event = {
            'request': {
                'data': {'image': 'binary data', 'prompt': 'private prompt'},
                'cookies': {'sessionid': 'secret'},
                'headers': {'Authorization': 'secret', 'X-CSRFToken': 'secret', 'Content-Type': 'image/png'},
            },
            'extra': {'extracted_text': 'private OCR', 'safe_value': 'kept'},
            'contexts': {'extraction': {'optimized_prompt': 'private prompt'}},
        }

        scrubbed = before_send(event, {})

        self.assertNotIn('data', scrubbed['request'])
        self.assertNotIn('cookies', scrubbed['request'])
        self.assertEqual(scrubbed['request']['headers']['Authorization'], '[Filtered]')
        self.assertEqual(scrubbed['request']['headers']['X-CSRFToken'], '[Filtered]')
        self.assertEqual(scrubbed['request']['headers']['Content-Type'], 'image/png')
        self.assertEqual(scrubbed['extra']['extracted_text'], '[Filtered]')
        self.assertEqual(scrubbed['extra']['safe_value'], 'kept')
        self.assertEqual(scrubbed['contexts']['extraction']['optimized_prompt'], '[Filtered]')

    def test_capture_exception_attaches_metadata_without_text(self):
        extraction = self._create_queued_extraction()

        with patch('api.observability.sentry_sdk.capture_exception') as mock_capture:
            capture_exception(
                RuntimeError('OCR unavailable'),
                operation='extraction_processing',
                extraction=extraction,
                context={'processing_time_ms': 123},
            )

        mock_capture.assert_called_once()

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


class PromptOptimizerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='optimizer-user', email='optimizer@example.com')
        self.client.force_authenticate(self.user)

    def test_optimizer_extracts_components_and_builds_generic_prompt(self):
        result = optimize_prompt('woman walking in Tokyo at night, neon lights, cinematic, 35mm')

        self.assertEqual(result.template, 'generic')
        self.assertEqual(result.components['subject'], ['woman'])
        self.assertEqual(result.components['action'], ['walking'])
        self.assertEqual(result.components['environment'], ['Tokyo at night'])
        self.assertEqual(result.components['lighting'], ['neon lights'])
        self.assertEqual(result.components['camera'], ['35mm lens'])
        self.assertEqual(
            result.optimized_prompt,
            'A cinematic scene of a woman walking through Tokyo at night, illuminated by neon lights, captured with 35mm lens.',
        )

    def test_optimizer_selects_portrait_template(self):
        result = optimize_prompt('cinematic portrait of a smiling woman, soft lighting, 50mm')

        self.assertEqual(result.template, 'portrait')
        self.assertIn('cinematic portrait', result.optimized_prompt)
        self.assertIn('smiling', result.optimized_prompt)
        self.assertIn('captured with 50mm lens', result.optimized_prompt)

    def test_optimizer_does_not_invent_missing_components(self):
        result = optimize_prompt('woman walking in Tokyo')

        self.assertNotIn('highly detailed', result.optimized_prompt)
        self.assertNotIn('lighting', result.optimized_prompt)
        self.assertNotIn('captured with', result.optimized_prompt)

    def test_optimizer_accepts_classifier_signal_objects(self):
        classification = classify_prompt_text('cinematic portrait, 35mm lens, highly detailed')
        result = optimize_prompt('woman in a studio', classification.matched_signals)

        self.assertEqual(result.components['style'], ['cinematic'])
        self.assertEqual(result.components['camera'], ['35mm lens'])
        self.assertEqual(result.components['quality'], ['highly detailed'])

    def test_optimizer_handles_empty_text(self):
        result = optimize_prompt('')

        self.assertEqual(result.optimized_prompt, '')
        self.assertEqual(result.components, {})

    def test_optimizer_preserves_unmatched_details_in_long_prompt(self):
        result = optimize_prompt(
            'close-up portrait of a man with thick messy hair, a neatly trimmed beard, '
            'dark sunglasses, and a dark button-up shirt, soft lighting'
        )

        self.assertEqual(result.template, 'portrait')
        self.assertIn('thick messy hair', result.optimized_prompt)
        self.assertIn('dark sunglasses', result.optimized_prompt)

    def test_detail_endpoint_backfills_optimizer_for_legacy_completed_record(self):
        extraction = Extraction.objects.create(
            user=self.user,
            image=_build_image_file(),
            original_filename='legacy.png',
            file_size=1,
            content_type='image/png',
            status=Extraction.Status.COMPLETED,
            extracted_text='cinematic portrait of a woman, soft lighting',
            classification_label='uncertain',
            matched_signals=[],
            message='OCR completed, but prompt evidence is limited.',
        )

        response = self.client.get(f'/api/v1/extractions/{extraction.id}/')

        extraction.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['optimized_prompt'])
        self.assertEqual(extraction.optimizer_version, 'rule-based-v2')


class OCRTextCleaningTests(APITestCase):
    def test_removes_standalone_username_and_timestamp_metadata(self):
        raw = """lemonkasha 21h
@creator 3h
9:08 PM
12K likes
A cinematic portrait of a woman"""

        self.assertEqual(clean_extracted_text(raw), 'A cinematic portrait of a woman')

    def test_preserves_metadata_like_text_inside_prompt_content(self):
        raw = 'A woman in a 21h neon city scene with 12K lights'

        self.assertEqual(clean_extracted_text(raw), raw)

    def test_removes_wrappers_social_footer_and_numbering(self):
        raw = """1. Here's the prompt
Cinematic portrait of a woman
standing in a rainy Tokyo street

Follow @xyz
Like & Share

35mm lens
shallow depth of field"""
        self.assertEqual(
            clean_extracted_text(raw),
            "Cinematic portrait of a woman\nstanding in a rainy Tokyo street\n35mm lens\nshallow depth of field",
        )

    def test_removes_emoji_urls_handles_and_hashtags_on_noise_lines(self):
        raw = "✨✨\nhttps://example.com/prompt\n@creator\n#aiart\nA cinematic portrait"
        self.assertEqual(clean_extracted_text(raw), "A cinematic portrait")

    def test_preserves_words_that_are_meaningful_inside_prompt_lines(self):
        raw = "Share light across the face\nFollow the subject with a shallow depth of field"
        self.assertEqual(clean_extracted_text(raw), raw)

    def test_noise_only_text_returns_empty(self):
        self.assertEqual(clean_extracted_text("Copy this prompt\n👍\nSave this\n@creator"), "")

    def test_removes_reference_screenshot_headers_and_footer_ctas(self):
        raw = """PROMPT:
Create a realistic cinematic portrait of a man and a lion.
Suggested settings:
Style: Ultra-realistic, cinematic, 8K
Save this!
SWIPE <<<
/prompt"""
        self.assertEqual(
            clean_extracted_text(raw),
            "Create a realistic cinematic portrait of a man and a lion.\n"
            "Suggested settings:\n"
            "Style: Ultra-realistic, cinematic, 8K",
        )

    def test_removes_wrappers_when_attached_to_prompt_text(self):
        raw = (
            "Copy prompt 👉 Create a moody editorial portrait\n"
            "Paste the prompt here: Use soft winter light\n"
            "PROMPT: A detailed face with natural skin texture\n"
            "A detailed face, natural skin texture | Save this prompt"
        )
        self.assertEqual(
            clean_extracted_text(raw),
            "Create a moody editorial portrait\n"
            "Use soft winter light\n"
            "A detailed face with natural skin texture\n"
            "A detailed face, natural skin texture",
        )

    def test_removes_merged_follow_footer(self):
        self.assertEqual(clean_extracted_text("Follow me for more"), "")

    def test_worker_stores_raw_and_cleaned_text_and_classifies_cleaned_text(self):
        extraction = Extraction.objects.create(
            image=_build_image_file(),
            original_filename='prompt.png',
            file_size=1,
            content_type='image/png',
            status=Extraction.Status.QUEUED,
            message='Image received. OCR job queued.',
        )
        raw = 'lemonkasha 21h\nCinematic portrait, 35mm lens\nFollow @creator\nLike & Share'
        with patch('api.tasks.extract_prompt_text_from_path', return_value=raw):
            status = process_extraction_job(str(extraction.id))

        extraction.refresh_from_db()
        self.assertEqual(status, Extraction.Status.COMPLETED)
        self.assertEqual(extraction.raw_ocr_text, raw)
        self.assertEqual(extraction.extracted_text, 'Cinematic portrait, 35mm lens')
        self.assertEqual(extraction.classification_label, 'prompt')

    def test_cleanup_backfill_command_repairs_existing_record(self):
        extraction = Extraction.objects.create(
            image=_build_image_file(),
            original_filename='legacy-noise.png',
            file_size=1,
            content_type='image/png',
            status=Extraction.Status.COMPLETED,
            raw_ocr_text='lemonkasha 21h\nCinematic portrait of a woman',
            extracted_text='lemonkasha 21h\nCinematic portrait of a woman',
            classification_label='uncertain',
        )

        call_command('backfill_extraction_cleanup')

        extraction.refresh_from_db()
        self.assertEqual(extraction.extracted_text, 'Cinematic portrait of a woman')
        self.assertNotIn('lemonkasha', extraction.optimized_prompt)


class OCRLayoutSelectionTests(SimpleTestCase):
    def test_normalized_ocr_lines_retain_boxes_and_scores(self):
        lines = _normalize_ocr_result(
            [{
                'rec_texts': ['PROMPT:', 'A cinematic portrait'],
                'rec_scores': [0.99, 0.95],
                'rec_boxes': [[30, 80, 220, 115], [30, 160, 600, 190]],
            }],
            image_height=875,
        )

        self.assertEqual([line.text for line in lines], ['PROMPT:', 'A cinematic portrait'])
        self.assertEqual(lines[0].box, (30.0, 80.0, 220.0, 115.0))
        self.assertEqual(lines[1].score, 0.95)

    @patch('api.ocr._embedded_image_regions')
    def test_anchor_selection_excludes_text_inside_embedded_image(self, mock_regions):
        mock_regions.return_value = [(260, 444, 632, 817)]
        lines = [
            OCRTextLine('PROMPT:', 0.99, (30, 88, 220, 115)),
            OCRTextLine('Main prompt paragraph', 0.98, (30, 160, 610, 190)),
            OCRTextLine('Prompt text beside image', 0.97, (30, 450, 240, 480)),
            OCRTextLine('Bestsellers of the week', 0.96, (286, 520, 450, 600)),
        ]

        selected = _select_prompt_lines(lines, '/tmp/reference.png')

        self.assertEqual(
            [line.text for line in selected],
            ['PROMPT:', 'Main prompt paragraph', 'Prompt text beside image'],
        )

    @patch('api.ocr._embedded_image_regions', return_value=[])
    def test_anchorless_selection_keeps_dominant_prompt_block(self, _mock_regions):
        lines = [
            OCRTextLine('9:16 vertical, photoreal cyberpunk scene', 0.98, (55, 220, 600, 250)),
            OCRTextLine('Dense purple fog and cinematic lighting', 0.98, (55, 255, 600, 285)),
            OCRTextLine('@creator_handle', 0.99, (275, 820, 390, 840)),
        ]

        selected = _select_prompt_lines(lines, '/tmp/reference.png')

        self.assertEqual(
            [line.text for line in selected],
            ['9:16 vertical, photoreal cyberpunk scene', 'Dense purple fog and cinematic lighting'],
        )


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
