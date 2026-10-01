from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
import json
import re
from typing import Any, Iterable


OPTIMIZER_VERSION = 'rule-based-v2'


@dataclass(frozen=True)
class PromptComponents:
    subject: list[str] = field(default_factory=list)
    action: list[str] = field(default_factory=list)
    environment: list[str] = field(default_factory=list)
    lighting: list[str] = field(default_factory=list)
    style: list[str] = field(default_factory=list)
    camera: list[str] = field(default_factory=list)
    quality: list[str] = field(default_factory=list)
    composition: list[str] = field(default_factory=list)
    clothing: list[str] = field(default_factory=list)
    expression: list[str] = field(default_factory=list)
    atmosphere: list[str] = field(default_factory=list)
    background: list[str] = field(default_factory=list)
    product: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {
            name: values
            for name, values in self.__dict__.items()
            if values
        }


@dataclass(frozen=True)
class OptimizerResult:
    optimized_prompt: str
    template: str
    components: dict[str, list[str]]
    optimizer_version: str = OPTIMIZER_VERSION


def _load_component_rules() -> tuple[dict[str, Any], ...]:
    package = resources.files(__package__).joinpath('knowledge').joinpath('components.json')
    payload = json.loads(package.read_text(encoding='utf-8'))
    return tuple(payload.get('signals', []))


def _normalize(value: str) -> str:
    return re.sub(r'\s+', ' ', value.casefold()).strip()


def _phrase_pattern(value: str) -> re.Pattern[str]:
    parts = [_normalize(part) for part in value.split() if part]
    return re.compile(r'\b' + r'\s+'.join(re.escape(part) for part in parts) + r'\b', re.IGNORECASE)


def _add_component(target: dict[str, list[str]], category: str, value: str) -> None:
    value = re.sub(r'\s+', ' ', value).strip(' ,.;:')
    if not value:
        return
    target.setdefault(category, [])
    if value.casefold() not in {item.casefold() for item in target[category]}:
        target[category].append(value)


def _match_component_rules(text: str) -> tuple[dict[str, list[str]], list[tuple[int, int]]]:
    matches: list[tuple[int, int, int, str, str]] = []
    for rule in _load_component_rules():
        canonical = str(rule.get('text', '')).strip()
        category = str(rule.get('category', '')).strip()
        if not canonical or not category:
            continue
        for phrase in [canonical, *rule.get('aliases', [])]:
            phrase = str(phrase).strip()
            if not phrase:
                continue
            for found in _phrase_pattern(phrase).finditer(text):
                matches.append((found.start(), found.end(), len(phrase), category, canonical))

    # Prefer longer phrases and never let an alias overlap a more specific match.
    occupied: list[tuple[int, int]] = []
    components: dict[str, list[str]] = {}
    for start, end, _length, category, canonical in sorted(
        matches,
        key=lambda item: (-item[2], item[0], item[1]),
    ):
        if any(start < other_end and end > other_start for other_start, other_end in occupied):
            continue
        occupied.append((start, end))
        _add_component(components, category, canonical)

    return components, occupied


def _merge_classifier_signals(
    components: dict[str, list[str]],
    matched_signals: Iterable[Any] | None,
) -> None:
    category_map = {
        'style': 'style',
        'lighting': 'lighting',
        'camera': 'camera',
        'quality': 'quality',
        'composition': 'composition',
    }
    for signal in matched_signals or []:
        category = getattr(signal, 'category', None) or signal.get('category')
        polarity = getattr(signal, 'polarity', None) or signal.get('polarity')
        value = getattr(signal, 'text', None) or signal.get('text')
        if polarity != 'positive' or category not in category_map:
            continue
        _add_component(components, category_map[category], str(value))


def _remaining_context(text: str, spans: list[tuple[int, int]]) -> str:
    pieces: list[str] = []
    cursor = 0
    for start, end in sorted(spans):
        pieces.append(text[cursor:start])
        cursor = end
    pieces.append(text[cursor:])
    context = ' '.join(pieces)
    context = re.sub(r'[\n,;|]+', ' ', context)
    context = re.sub(r'\s+', ' ', context).strip(' .,:;-')
    context = re.sub(
        r'^(?:(?:a|an|the)\s+)?(?:image|scene|of|featuring|showing)\s+(?:an?\s+)?',
        '',
        context,
        flags=re.IGNORECASE,
    )
    context = re.sub(r'^(?:create|show|depict|depicting|make)\s+(?:an?\s+)?', '', context, flags=re.IGNORECASE)
    context = re.sub(r'\bwith an?\s*(?=[.,])', '', context, flags=re.IGNORECASE)
    context = re.sub(r'\bthe lighting is\s*$', '', context, flags=re.IGNORECASE)
    context = re.sub(r'\s+', ' ', context).strip(' .,:;-')
    context = re.sub(r'\s+([,.])', r'\1', context)
    return context


def _infer_missing_components(components: dict[str, list[str]], context: str) -> None:
    if not context:
        return
    words = context.split()
    if not components.get('subject'):
        # Keep this deliberately conservative: only use a short remaining phrase
        # as a subject when there is no competing sentence structure.
        if len(words) <= 5 and not re.search(r'\b(?:with|through|against|under|during)\b', context, re.I):
            _add_component(components, 'subject', context)


def _add_unmatched_details(components: dict[str, list[str]], context: str) -> None:
    if len(context.split()) < 2:
        return
    if context.casefold() in {'in', 'of', 'with', 'and', 'the subject'}:
        return
    _add_component(components, 'details', context)


def _first(components: dict[str, list[str]], category: str, fallback: str = '') -> str:
    values = components.get(category, [])
    return values[0] if values else fallback


def _join_parts(parts: list[str]) -> str:
    value = re.sub(r'\s+', ' ', ' '.join(part.strip() for part in parts if part.strip()))
    return re.sub(r'\s+([,.;])', r'\1', value).strip(' ,')


def _with_article(value: str) -> str:
    if value.casefold().startswith(('a ', 'an ', 'the ')):
        return value
    if value.casefold()[:1] in {'a', 'e', 'i', 'o', 'u'}:
        return f'an {value}'
    return f'a {value}'


def _generic_prompt(components: dict[str, list[str]]) -> str:
    style = _first(components, 'style')
    subject = _first(components, 'subject', 'the subject')
    action = _first(components, 'action')
    environment = _first(components, 'environment')
    lighting = _first(components, 'lighting')
    quality = _first(components, 'quality')
    camera = _first(components, 'camera')
    details = _first(components, 'details')

    subject_phrase = f'{_with_article(subject)} {action}'.strip() if action else _with_article(subject)
    if environment:
        subject_phrase += f' through {environment}' if action else f' in {environment}'
    parts = [f'A {style} scene of {subject_phrase}' if style else f'A scene of {subject_phrase}']
    if quality:
        parts.append(f', {quality}')
    if lighting:
        parts.append(f', illuminated by {lighting}')
    if camera:
        parts.append(f', captured with {camera}')
    if details and details.casefold() != subject_phrase.casefold():
        parts.append(f', {details}')
    return _join_parts(parts) + '.'


def _template_prompt(template: str, components: dict[str, list[str]]) -> str:
    style = _first(components, 'style')
    subject = _first(components, 'subject', 'the subject')
    environment = _first(components, 'environment')
    lighting = _first(components, 'lighting')
    camera = _first(components, 'camera')
    composition = _first(components, 'composition')
    clothing = _first(components, 'clothing')
    action = _first(components, 'action')
    expression = _first(components, 'expression')
    background = _first(components, 'background') or environment
    product = _first(components, 'product', subject)
    atmosphere = _first(components, 'atmosphere')
    details = _first(components, 'details')

    if template == 'portrait':
        parts = [f'A {style} portrait of {_with_article(subject)}' if style else f'A portrait of {_with_article(subject)}']
        if expression:
            parts.append(f', {expression}')
        if lighting:
            parts.append(f', {lighting}')
        if background:
            parts.append(f', against {background}')
        if camera:
            parts.append(f', captured with {camera}')
        if details:
            parts.append(f', {details}')
        return _join_parts(parts) + '.'
    if template == 'landscape':
        parts = [f'A {style} landscape featuring {_with_article(subject)}' if style else f'A landscape featuring {_with_article(subject)}']
        if environment:
            parts.append(f', set in {environment}')
        if lighting:
            parts.append(f', with {lighting}')
        if atmosphere:
            parts.append(f' and {atmosphere}')
        if composition:
            parts.append(f', using {composition}')
        if details:
            parts.append(f', {details}')
        return _join_parts(parts) + '.'
    if template == 'character':
        parts = [f'A {style} character design of {_with_article(subject)}' if style else f'A character design of {_with_article(subject)}']
        if clothing:
            parts.append(f', wearing {clothing}')
        if action:
            parts.append(f', {action}')
        if environment:
            parts.append(f', set against {environment}')
        if lighting:
            parts.append(f', with {lighting}')
        if details:
            parts.append(f', {details}')
        return _join_parts(parts) + '.'
    if template == 'product':
        parts = [f'A {style} product photograph of {product}' if style else f'A product photograph of {product}']
        if environment:
            parts.append(f', placed in {environment}')
        if lighting:
            parts.append(f', featuring {lighting}')
        if composition:
            parts.append(f' and {composition}')
        if background:
            parts.append(f', with {background}')
        if details:
            parts.append(f', {details}')
        return _join_parts(parts) + '.'
    return _generic_prompt(components)


def _select_template(components: dict[str, list[str]], text: str) -> str:
    lowered = text.casefold()
    if components.get('product') or re.search(r'\b(product|packaging|bottle|shoe|watch|perfume)\b', lowered):
        return 'product'
    if components.get('clothing') or re.search(r'\b(character design|costume|armor|outfit)\b', lowered):
        return 'character'
    if components.get('expression') or 'portrait' in lowered or components.get('composition', []) and 'portrait' in components['composition']:
        return 'portrait'
    if components.get('atmosphere') or re.search(r'\b(landscape|mountain|valley|forest|ocean|lake|desert)\b', lowered):
        return 'landscape'
    return 'generic'


def optimize_prompt(text: str, matched_signals: Iterable[Any] | None = None) -> OptimizerResult:
    normalized = re.sub(r'\s+', ' ', text or '').strip()
    if not normalized:
        return OptimizerResult('', 'generic', {})

    components, spans = _match_component_rules(normalized)
    _merge_classifier_signals(components, matched_signals)
    context = _remaining_context(normalized, spans)
    _infer_missing_components(components, context)
    _add_unmatched_details(components, context)
    template = _select_template(components, normalized)
    return OptimizerResult(
        optimized_prompt=_template_prompt(template, components),
        template=template,
        components=components,
    )
