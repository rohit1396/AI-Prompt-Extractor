from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import sentry_sdk


def capture_exception(
    exception: BaseException,
    *,
    operation: str,
    extraction: Any = None,
    user: Any = None,
    tags: Mapping[str, str] | None = None,
    context: Mapping[str, Any] | None = None,
) -> None:
    """Capture an application exception without sending extraction content."""
    with sentry_sdk.push_scope() as scope:
        scope.set_tag('operation', operation)
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        if extraction is not None:
            scope.set_tag('extraction_id', str(extraction.id))
            scope.set_tag('extraction_status', str(extraction.status))
            scope.set_tag('storage_provider', str(extraction.storage_provider))
            scope.set_context(
                'extraction',
                {
                    'id': str(extraction.id),
                    'status': str(extraction.status),
                    'filename_extension': extraction.original_filename.rsplit('.', 1)[-1].lower()
                    if '.' in extraction.original_filename
                    else '',
                    'content_type': extraction.content_type,
                    'file_size': extraction.file_size,
                },
            )
            if extraction.user_id:
                scope.set_user({'id': str(extraction.user_id), 'email': extraction.user.email})
        elif user is not None and getattr(user, 'is_authenticated', False):
            scope.set_user({'id': str(user.id), 'email': user.email})

        if context:
            scope.set_context('application', dict(context))

        sentry_sdk.capture_exception(exception)
