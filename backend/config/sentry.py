from __future__ import annotations

from typing import Any


SENSITIVE_KEYS = {
    'body',
    'cookie',
    'cookies',
    'authorization',
    'credential',
    'image',
    'image_data',
    'ocr_text',
    'raw_ocr_text',
    'extracted_text',
    'prompt',
    'optimized_prompt',
}


def _remove_sensitive_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: '[Filtered]' if key.lower() in SENSITIVE_KEYS else _remove_sensitive_values(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_remove_sensitive_values(item) for item in value]
    return value


def before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
    request = event.get('request')
    if isinstance(request, dict):
        request.pop('data', None)
        request.pop('cookies', None)
        headers = request.get('headers')
        if isinstance(headers, dict):
            request['headers'] = {
                key: '[Filtered]' if key.lower() in {'authorization', 'cookie', 'x-csrftoken'} else value
                for key, value in headers.items()
            }

    if isinstance(event.get('extra'), dict):
        event['extra'] = _remove_sensitive_values(event['extra'])
    if isinstance(event.get('contexts'), dict):
        event['contexts'] = _remove_sensitive_values(event['contexts'])

    return event
