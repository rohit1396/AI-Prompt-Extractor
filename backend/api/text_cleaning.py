"""Conservative, line-aware cleanup for OCR captured from prompt screenshots."""

from __future__ import annotations

import re
import unicodedata


_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_HANDLE_RE = re.compile(r"@[a-z0-9_.-]+", re.IGNORECASE)
_HASHTAG_RE = re.compile(r"#[\w-]+", re.UNICODE)
_NUMBER_PREFIX_RE = re.compile(r"^\s*(?:\d+[.)]|[-*•‣◦▪‒–—])\s*")
_PROMPT_HEADER_RE = re.compile(r"^/?prompt\s*[:\-–—.!|]*$", re.IGNORECASE)
_LEADING_PROMPT_LABEL_RE = re.compile(
    r"^(?:/?prompt|(?:here(?:'|’)s|here is|this is)\s+(?:the\s+)?prompt|"
    r"(?:the\s+)?prompt\s+(?:is\s+)?below)\s*[:\-–—.!|]+\s*",
    re.IGNORECASE,
)
_WRAPPER_RE = re.compile(
    r"^(?:here(?:'|’)s|here is|this is)\s+(?:the\s+)?prompt$"
    r"|^(?:copy|paste|use)\s+(?:this\s+)?prompt(?:\s+here)?$"
    r"|^(?:the\s+)?prompt\s+(?:is\s+)?below$"
    r"|^(?:paste|copy)\s+(?:the\s+)?prompt\s+here$",
    re.IGNORECASE,
)
_CTA_RE = re.compile(
    r"^(?:(?:please\s+)?(?:follow|like|share|comment|save|subscribe)"
    r"(?:\s+(?:this|below|for\s+more|this\s+prompt))?\s*[.!,:;|&+\-]*\s*)+$"
    r"|^(?:like\s*(?:&|and)\s*share)$"
    r"|^(?:follow|save)\s+(?:me\s+)?for\s+more\s*[.!,:;|&+\-]*$"
    r"|^swipe(?:\s+(?:left|right))?\s*[<>&|!.-]*$",
    re.IGNORECASE,
)
_LEADING_WRAPPER_RE = re.compile(
    r"^(?:copy|paste|use)\s+(?:this\s+|the\s+)?prompt\s*(?:here)?\s*"
    r"(?:[:.!|\-–—👉➡]+\s*)?",
    re.IGNORECASE,
)
_TRAILING_CTA_RE = re.compile(
    r"(?:\s*[|•·—–-]*\s*)(?:save\s+(?:this|this\s+prompt)|"
    r"follow\s+(?:me|for\s+more)|like\s*(?:&|and)\s*share|"
    r"swipe(?:\s+(?:left|right))?)\s*[<>&|!.-]*$",
    re.IGNORECASE,
)
_EMOJI_RE = re.compile(
    "["
    "\\U0001F1E6-\\U0001F1FF"  # flags
    "\\U0001F300-\\U0001FAFF"  # pictographs and emoji
    "\\u2600-\\u27BF"          # miscellaneous symbols/dingbats
    "]+",
    re.UNICODE,
)


def _without_emoji(value: str) -> str:
    return _EMOJI_RE.sub("", value)


def _is_noise_line(line: str) -> bool:
    candidate = line.strip()
    if not candidate:
        return True

    without_emoji = _without_emoji(candidate).strip()
    if not without_emoji:
        return True

    normalized = re.sub(r"\s+", " ", without_emoji).strip()
    normalized = normalized.strip(" .,:;|!?")
    if not normalized:
        return True
    if _PROMPT_HEADER_RE.fullmatch(normalized):
        return True
    if _WRAPPER_RE.fullmatch(normalized):
        return True
    if _CTA_RE.fullmatch(normalized):
        return True
    if _URL_RE.fullmatch(normalized) or _HANDLE_RE.fullmatch(normalized) or _HASHTAG_RE.fullmatch(normalized):
        return True

    # CTA lines that append only a handle, URL, or hashtag are still noise.
    cta_prefix = re.match(r"^(?:follow|like|share|comment|save|subscribe)\b", normalized, re.IGNORECASE)
    if cta_prefix:
        remainder = normalized[cta_prefix.end():].strip(" .,:;|!?")
        remainder = re.sub(r"(?:&|and)\s*(?:like|share)\b", "", remainder, flags=re.IGNORECASE).strip()
        if not remainder or any(pattern.fullmatch(remainder) for pattern in (_URL_RE, _HANDLE_RE, _HASHTAG_RE)):
            return True
    return False


def clean_extracted_text(text: str) -> str:
    """Remove common screenshot wrappers and social noise while preserving prompt lines."""
    cleaned_lines: list[str] = []
    for raw_line in unicodedata.normalize("NFKC", text or "").splitlines():
        line = _without_emoji(raw_line)
        line = _NUMBER_PREFIX_RE.sub("", line)
        line = " ".join(line.split()).strip()
        line = _LEADING_PROMPT_LABEL_RE.sub("", line).strip()
        line = _LEADING_WRAPPER_RE.sub("", line).strip()
        line = _TRAILING_CTA_RE.sub("", line).strip()
        if not line or _is_noise_line(line):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()
