from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib import resources
import json
import re
import unicodedata
from typing import Any

CLASSIFIER_VERSION = 'prompt-rule-v2'
PROMPT_EVIDENCE_TARGET = 30
PROMPT_SCORE_THRESHOLD = 10
NOT_PROMPT_NEGATIVE_THRESHOLD = 6


@dataclass(frozen=True)
class MatchedSignal:
    text: str
    category: str
    weight: int
    polarity: str


@dataclass(frozen=True)
class ClassificationResult:
    is_prompt: bool
    confidence: int
    label: str
    score: int
    matched_signals: list[MatchedSignal]
    classifier_version: str = CLASSIFIER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize('NFKC', text or '').lower()
    return re.sub(r'\s+', ' ', normalized).strip()


@lru_cache(maxsize=2)
def _load_signal_file(filename: str) -> tuple[tuple[dict[str, Any], ...], dict[str, int]]:
    package = resources.files(__package__).joinpath('knowledge').joinpath(filename)
    payload = json.loads(package.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError(f'{filename} must contain a signal object.')

    signals = payload.get('signals', [])
    caps = payload.get('category_caps', {})
    if not isinstance(signals, list) or not isinstance(caps, dict):
        raise ValueError(f'{filename} has an invalid signal schema.')
    return tuple(signals), {str(category): int(cap) for category, cap in caps.items()}


def _signal_matches(text: str, signal_text: str) -> bool:
    term = normalize_text(signal_text)
    if not term:
        return False
    if re.fullmatch(r'[\w\s]+', term):
        pattern = r'\b' + r'\s+'.join(re.escape(part) for part in term.split()) + r'\b'
        return re.search(pattern, text) is not None
    return term in text


def _matches_signal(text: str, signal: dict[str, Any]) -> bool:
    terms = [signal.get('text', '')] + list(signal.get('aliases', []))
    return any(_signal_matches(text, str(term)) for term in terms)


def _collect_matches(text: str) -> tuple[list[MatchedSignal], dict[str, int], dict[str, int]]:
    matches: list[MatchedSignal] = []
    positive_totals: dict[str, int] = {}
    negative_totals: dict[str, int] = {}

    for filename, polarity, totals in (
        ('positive_signals.json', 'positive', positive_totals),
        ('negative_signals.json', 'negative', negative_totals),
    ):
        signals, category_caps = _load_signal_file(filename)
        for signal in signals:
            if not _matches_signal(text, signal):
                continue
            canonical_text = str(signal.get('text', '')).strip()
            category = str(signal.get('category', 'general')).strip() or 'general'
            weight = max(0, int(signal.get('weight', 0)))
            remaining = max(0, category_caps.get(category, weight) - totals.get(category, 0))
            contribution = min(weight, remaining)
            if contribution == 0:
                continue
            totals[category] = totals.get(category, 0) + contribution
            matches.append(MatchedSignal(canonical_text, category, contribution, polarity))
    return matches, positive_totals, negative_totals


def _has_strong_prompt_signal(matches: list[MatchedSignal]) -> bool:
    return any(signal.polarity == 'positive' and signal.weight >= 8 for signal in matches)


def _evidence_coverage(net_score: int) -> int:
    """Return explainable prompt evidence coverage, not a probability."""
    return max(0, min(99, round(100 * max(0, net_score) / PROMPT_EVIDENCE_TARGET)))


def classify_prompt_text(text: str) -> ClassificationResult:
    normalized = normalize_text(text)
    if not normalized:
        return ClassificationResult(False, 0, 'uncertain', 0, [])

    matches, positive_totals, negative_totals = _collect_matches(normalized)
    positive_score = sum(positive_totals.values())
    negative_score = sum(negative_totals.values())
    category_count = len(positive_totals)
    diversity_bonus = min(8, max(0, category_count - 1) * 2)
    score = positive_score + diversity_bonus - negative_score

    if negative_score >= NOT_PROMPT_NEGATIVE_THRESHOLD and negative_score >= positive_score + 3:
        label = 'not_prompt'
    elif (
        score >= PROMPT_SCORE_THRESHOLD
        and (category_count >= 2 or _has_strong_prompt_signal(matches))
    ):
        label = 'prompt'
    else:
        label = 'uncertain'

    return ClassificationResult(
        is_prompt=label == 'prompt',
        confidence=_evidence_coverage(score),
        label=label,
        score=score,
        matched_signals=matches,
    )
