"""
OCR extraction helpers kept for the future background worker path.

Step 1 of the async split intentionally removes OCR from the HTTP upload
request. Keep this module intact so the worker can import it later without
having to reconstruct the PaddleOCR pipeline.
"""

from __future__ import annotations

import os
import re
from tempfile import NamedTemporaryFile
from dataclasses import dataclass
from typing import Any, Sequence

try:
    import cv2
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - dependency is present in production
    cv2 = None
    np = None
from PIL import Image, ImageOps
import logging

logger = logging.getLogger(__name__)

_OCR_ENGINE: Any | None = None
_MAX_IMAGE_DIMENSION = 1600
_PROMPT_ANCHOR_RE = re.compile(
    r"^(?:/?prompt|copy\s+(?:this\s+|the\s+)?prompt|"
    r"(?:here(?:'|’)s|here\s+is|this\s+is)\s+(?:the\s+)?prompt|"
    r"(?:the\s+)?prompt\s+(?:is\s+)?below)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class OCRTextLine:
    text: str
    score: float | None
    box: tuple[float, float, float, float] | None

    @property
    def center(self) -> tuple[float, float] | None:
        if self.box is None:
            return None
        x1, y1, x2, y2 = self.box
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @property
    def height(self) -> float:
        if self.box is None:
            return 0.0
        return max(0.0, self.box[3] - self.box[1])


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


def _coerce_box(raw_box: Any) -> tuple[float, float, float, float] | None:
    try:
        if raw_box is None or len(raw_box) < 4:
            return None
        x1, y1, x2, y2 = (float(value) for value in raw_box[:4])
    except (TypeError, ValueError):
        return None
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _normalize_ocr_result(result: Any, image_height: int | None) -> list[OCRTextLine]:
    lines: list[OCRTextLine] = []
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

            box = _coerce_box(boxes[index] if index < len(boxes) else None)
            if image_height and box is not None:
                center_y = (box[1] + box[3]) / 2
                vertical_position = center_y / image_height
                if vertical_position < 0.06 or vertical_position > 0.94:
                    continue

            score_value = None
            if score is not None:
                try:
                    score_value = float(score)
                except (TypeError, ValueError):
                    pass
            lines.append(OCRTextLine(text=text, score=score_value, box=box))

    return lines


def _find_prompt_anchor(lines: Sequence[OCRTextLine]) -> OCRTextLine | None:
    for line in sorted(lines, key=lambda item: ((item.box or (0, 0, 0, 0))[1], (item.box or (0, 0, 0, 0))[0])):
        if _PROMPT_ANCHOR_RE.search(line.text.strip()):
            return line
    return None


def _embedded_image_regions(source_path: str) -> list[tuple[float, float, float, float]]:
    """Find conservative, large rectangular regions likely to be embedded images."""
    if cv2 is None or np is None:
        return []
    image = cv2.imread(source_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return []

    height, width = image.shape[:2]
    image_area = float(width * height)
    edges = cv2.Canny(image, 60, 160)
    edges = cv2.dilate(edges, np.ones((3, 3), dtype=np.uint8), iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    regions: list[tuple[float, float, float, float]] = []

    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, region_width, region_height = cv2.boundingRect(contour)
        region_area = float(region_width * region_height)
        if area < image_area * 0.08 or region_area < image_area * 0.10:
            continue
        if region_area > image_area * 0.82:
            continue
        if x <= width * 0.01 or y <= height * 0.01:
            continue
        rectangularity = area / region_area if region_area else 0.0
        aspect_ratio = region_width / float(region_height or 1)
        if rectangularity < 0.45 or not 0.25 <= aspect_ratio <= 4.0:
            continue
        candidate = (float(x), float(y), float(x + region_width), float(y + region_height))
        if not any(_intersection_over_min_area(candidate, existing) > 0.8 for existing in regions):
            regions.append(candidate)

    return regions


def _intersection_over_min_area(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    smallest_area = min(first_area, second_area)
    return intersection / smallest_area if smallest_area else 0.0


def _line_inside_region(line: OCRTextLine, region: tuple[float, float, float, float]) -> bool:
    if line.center is None:
        return False
    x, y = line.center
    return region[0] <= x <= region[2] and region[1] <= y <= region[3]


def _dominant_text_block(lines: Sequence[OCRTextLine]) -> set[int]:
    positioned = [(index, line) for index, line in enumerate(lines) if line.box is not None]
    if not positioned:
        return set(range(len(lines)))

    heights = sorted(line.height for _, line in positioned if line.height > 0)
    median_height = heights[len(heights) // 2] if heights else 16.0
    max_vertical_gap = max(48.0, median_height * 3.5)
    ordered = sorted(positioned, key=lambda item: (item[1].box[1], item[1].box[0]))
    groups: list[list[tuple[int, OCRTextLine]]] = []

    for item in ordered:
        if not groups:
            groups.append([item])
            continue
        previous_line = groups[-1][-1][1]
        vertical_gap = item[1].box[1] - previous_line.box[3]
        if vertical_gap <= max_vertical_gap:
            groups[-1].append(item)
        else:
            groups.append([item])

    largest_group = max(groups, key=lambda group: sum(len(line.text) for _, line in group))
    return {index for index, _ in largest_group}


def _select_prompt_lines(lines: Sequence[OCRTextLine], source_path: str) -> list[OCRTextLine]:
    if not lines:
        return []

    image_regions = _embedded_image_regions(source_path)
    candidates = [
        line for line in lines
        if not any(_line_inside_region(line, region) for region in image_regions)
    ]
    anchor = _find_prompt_anchor(candidates)

    if anchor is not None and anchor.box is not None:
        anchor_bottom = anchor.box[3]
        candidates = [
            line for line in candidates
            if line is anchor or line.box is None or line.box[1] >= anchor_bottom - max(anchor.height, 4.0)
        ]
    elif image_regions:
        candidate_indexes = _dominant_text_block(candidates)
        candidates = [line for index, line in enumerate(candidates) if index in candidate_indexes]
    else:
        candidates = [line for index, line in enumerate(lines) if index in _dominant_text_block(lines)]

    return sorted(
        candidates,
        key=lambda line: ((line.box or (0, 0, 0, 0))[1], (line.box or (0, 0, 0, 0))[0]),
    )


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
        selected_lines = _select_prompt_lines(lines, preprocessed_path)
        logger.info(
            'OCR layout selection completed extraction_id=%s detected_lines=%s selected_lines=%s',
            extraction_id,
            len(lines),
            len(selected_lines),
        )
        return '\n'.join(line.text for line in selected_lines).strip()
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
