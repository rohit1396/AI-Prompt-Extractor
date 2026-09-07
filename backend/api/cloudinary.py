from __future__ import annotations

import logging
import os
from hashlib import sha1
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import time
from urllib.parse import urlparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CloudinaryUploadResult:
    public_id: str
    secure_url: str
    version: int | None = None
    format: str = ''


def cloudinary_is_enabled() -> bool:
    return bool(
        settings.USE_CLOUDINARY_STORAGE
        and settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )


def _cloudinary_upload_url(resource_type: str = 'image') -> str:
    return f'https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/{resource_type}/upload'


def _cloudinary_destroy_url(resource_type: str = 'image') -> str:
    return f'https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/{resource_type}/destroy'


def _cloudinary_signature(params: dict[str, object]) -> str:
    signing_values = [
        f'{key}={value}'
        for key, value in sorted(params.items())
        if key != 'api_key' and value not in (None, '')
    ]
    return sha1('&'.join(signing_values).encode('utf-8') + settings.CLOUDINARY_API_SECRET.encode('utf-8')).hexdigest()


def _safe_json(response: requests.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def upload_image_to_cloudinary(uploaded_file, *, public_id: str | None = None) -> CloudinaryUploadResult:
    if not cloudinary_is_enabled():
        raise RuntimeError('Cloudinary is not configured.')

    if hasattr(uploaded_file, 'seek'):
        try:
            uploaded_file.seek(0)
        except OSError:
            pass

    upload_name = os.path.basename(getattr(uploaded_file, 'name', 'upload')) or 'upload'
    content_type = getattr(uploaded_file, 'content_type', 'application/octet-stream')
    data: dict[str, object] = {
        'folder': settings.CLOUDINARY_UPLOAD_FOLDER,
        'overwrite': 'false',
        'use_filename': 'true',
        'unique_filename': 'true',
        'timestamp': int(time()),
        'api_key': settings.CLOUDINARY_API_KEY,
    }
    if public_id:
        data['public_id'] = public_id
    data['signature'] = _cloudinary_signature(data)

    response = requests.post(
        _cloudinary_upload_url(),
        files={'file': (upload_name, uploaded_file, content_type)},
        data=data,
        timeout=60,
    )

    response_data = _safe_json(response)
    if not response.ok:
        payload = response_data.get('error', {})
        message = payload.get('message') if isinstance(payload, dict) else None
        raise RuntimeError(message or response.text or 'Cloudinary upload failed.')

    return CloudinaryUploadResult(
        public_id=response_data['public_id'],
        secure_url=response_data['secure_url'],
        version=response_data.get('version'),
        format=response_data.get('format', ''),
    )


def delete_image_from_cloudinary(public_id: str) -> bool:
    if not cloudinary_is_enabled():
        return False

    data: dict[str, object] = {
        'public_id': public_id,
        'timestamp': int(time()),
        'api_key': settings.CLOUDINARY_API_KEY,
        'invalidate': 'true',
    }
    data['signature'] = _cloudinary_signature(data)

    response = requests.post(
        _cloudinary_destroy_url(),
        data=data,
        timeout=30,
    )

    if not response.ok:
        logger.warning(
            'Failed to delete Cloudinary asset public_id=%s status_code=%s body=%s',
            public_id,
            response.status_code,
            response.text,
        )
        return False

    return True


def download_remote_file(url: str) -> str:
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()

        suffix = Path(urlparse(url).path).suffix or '.png'
        with NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            return temp_file.name
