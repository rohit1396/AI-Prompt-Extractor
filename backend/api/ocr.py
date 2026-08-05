from __future__ import annotations

import os
from tempfile import NamedTemporaryFile

from PIL import Image
from paddleocr import PaddleOCR

_OCR_ENGINE: PaddleOCR | None = None


def _get_ocr_engine() -> PaddleOCR:
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        _OCR_ENGINE = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang='en',
            enable_mkldnn=False,
        )
    return _OCR_ENGINE


def extract_prompt_text(uploaded_file) -> str:
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

        ocr_engine = _get_ocr_engine()
        result = ocr_engine.ocr(source_path)

        image_width = image_height = None
        try:
            with Image.open(source_path) as image:
                image_width, image_height = image.size
        except Exception:
            image_width = image_height = None

        lines: list[str] = []
        noise_terms = {'promptstudyo', 'promptlens'}
        for page in result or []:
            texts = page.get('rec_texts', []) if hasattr(page, 'get') else getattr(page, 'rec_texts', [])
            scores = page.get('rec_scores', []) if hasattr(page, 'get') else getattr(page, 'rec_scores', [])
            boxes = page.get('rec_boxes', []) if hasattr(page, 'get') else getattr(page, 'rec_boxes', [])

            for index, raw_text in enumerate(texts or []):
                text = str(raw_text).strip()
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

        return '\n'.join(lines).strip()
    finally:
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
