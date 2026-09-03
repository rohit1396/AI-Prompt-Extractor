"""
OCR extraction helpers kept for the future background worker path.

Step 1 of the async split intentionally removes OCR from the HTTP upload
request. Keep this module intact so the worker can import it later without
having to reconstruct the PaddleOCR pipeline.
"""

from __future__ import annotations

import os
from tempfile import NamedTemporaryFile
from typing import Any

from PIL import Image, ImageOps
import logging

logger = logging.getLogger(__name__)

_OCR_ENGINE: Any | None = None
_MAX_IMAGE_DIMENSION = 1600


def _get_ocr_engine() -> Any:
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        logger.info('OCR engine init started')
        try:
            from paddleocr import PaddleOCR
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                'PaddleOCR is not installed. Install the backend dependencies before running OCR.'
            ) from exc

        _OCR_ENGINE = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang='en',
            enable_mkldnn=False,
        )
        logger.info('OCR engine init completed')
    return _OCR_ENGINE


def _preprocess_image_for_ocr(source_path: str) -> tuple[str, tuple[int, int]]:
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in {'RGB', 'L'}:
            image = image.convert('RGB')

        width, height = image.size
        longest_edge = max(width, height)
        if longest_edge > _MAX_IMAGE_DIMENSION:
            scale = _MAX_IMAGE_DIMENSION / float(longest_edge)
            resized_width = max(1, int(round(width * scale)))
            resized_height = max(1, int(round(height * scale)))
            image = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

        with NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            image.save(temp_file.name, format='PNG', optimize=True)
            return temp_file.name, image.size


def _normalize_ocr_result(result: Any, image_height: int | None) -> list[str]:
    lines: list[str] = []
    noise_terms = {'promptstudyo', 'promptlens'}

    for page in result or []:
        texts = page.get('rec_texts', []) if hasattr(page, 'get') else getattr(page, 'rec_texts', [])
        scores = page.get('rec_scores', []) if hasattr(page, 'get') else getattr(page, 'rec_scores', [])
        boxes = page.get('rec_boxes', []) if hasattr(page, 'get') else getattr(page, 'rec_boxes', [])

        for index, raw_text in enumerate(texts or []):
            text = ' '.join(str(raw_text).split()).strip()
            if not text or len(text) == 1 or text.lower() in noise_terms:
                continue

            score = scores[index] if index < len(scores) else None
            if score is not None and score < 0.5:
                continue

            if image_height and index < len(boxes):
                box = boxes[index]
                if box is not None and len(box) >= 4:
                    center_y = (float(box[1]) + float(box[3])) / 2
                    vertical_position = center_y / image_height
                    if vertical_position < 0.06 or vertical_position > 0.94:
                        continue

            lines.append(text)

    return lines


def extract_prompt_text_from_path(source_path: str, *, extraction_id: str | None = None) -> str:
    temp_paths: list[str] = []
    try:
        if not source_path or not os.path.exists(source_path):
            raise FileNotFoundError(f'Image file does not exist: {source_path}')

        preprocessed_path, (_, image_height) = _preprocess_image_for_ocr(source_path)
        temp_paths.append(preprocessed_path)
        logger.info(
            'STEP 2: image preprocessed for OCR extraction_id=%s source_path=%s preprocessed_path=%s',
            extraction_id,
            source_path,
            preprocessed_path,
        )

        logger.info(
            'OCR call starting extraction_id=%s source_path=%s',
            extraction_id,
            preprocessed_path,
        )
        ocr_engine = _get_ocr_engine()
        result = ocr_engine.ocr(preprocessed_path)
        logger.info(
            'OCR call completed extraction_id=%s source_path=%s',
            extraction_id,
            preprocessed_path,
        )

        lines = _normalize_ocr_result(result, image_height)
        return '\n'.join(lines).strip()
    finally:
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


def extract_prompt_text(uploaded_file, *, extraction_id: str | None = None) -> str:
    original_path = uploaded_file.temporary_file_path() if hasattr(uploaded_file, 'temporary_file_path') else None
    source_path = original_path
    temp_paths: list[str] = []

    try:
        if not (source_path and os.path.exists(source_path)):
            with NamedTemporaryFile(suffix=os.path.splitext(uploaded_file.name)[1] or '.png', delete=False) as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                source_path = temp_file.name
            temp_paths.append(source_path)
            logger.info(
                'STEP 2: image staged for OCR extraction_id=%s source_path=%s',
                extraction_id,
                source_path,
            )

        return extract_prompt_text_from_path(source_path, extraction_id=extraction_id)
    finally:
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
