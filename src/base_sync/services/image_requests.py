import os
import requests
from logging import getLogger
import urllib
import random
import string
import re

from ..models.image_requests import ImageRequestsConfig


class ImageRequestsService:
    """."""

    def __init__(
            self,
            config: ImageRequestsConfig,
    ):
        """."""
        self._config = config
        self._logger = getLogger(__name__)
        self._session = requests.Session()

    @classmethod
    def _extract_filename_parts(cls, cd_header: str) -> tuple[str, str] | None:
        match_cd = re.search(r'filename\*\s*=\s*[\w\-]*\'\'([^;\n]+)', cd_header)
        if match_cd:
            full_name = urllib.parse.unquote(match_cd.group(1))
        else:
            match_plain = re.search(r'filename\s*=\s*["\']?([^"\';]+)', cd_header)
            if match_plain:
                full_name = match_plain.group(1)
            else:
                return None

        base_name, ext = os.path.splitext(full_name)
        return base_name, ext

    @classmethod
    def _generate_url_safe_string(cls, length: int = 4) -> str:
        charset = string.ascii_letters + string.digits + '-_'
        return ''.join(random.choices(charset, k=length))

    def _make_url(self, path: str) -> str:
        return (f"{self._config.schema}://{self._config.host}:"
                f"{self._config.port}{self._config.path_prefix.rstrip('/')}/{path.lstrip('/')}")

    def save_image(self, image_id: str, dest_path: str) -> str:
        url = self._make_url(f'/files/{image_id}/download')
        response = self._session.get(url, stream=True)

        if not response.ok:
            self._logger.error(f"Ошибка получения изображения {image_id}: {response.status_code}")
            raise RuntimeError("Download failed")

        cd = response.headers.get('Content-Disposition', '')
        base_name, ext = self._extract_filename_parts(cd)

        save_path = os.path.join(dest_path, f"{image_id}{ext}")

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=self._config.chunk_size):
                if chunk:
                    f.write(chunk)

        return save_path

    def upload_image(self, image_path: str) -> str:
        rand_part = self._generate_url_safe_string(16)
        url = self._make_url(f'/files/{rand_part}')

        mime_type = 'application/octet-stream'
        import mimetypes
        guessed = mimetypes.guess_type(image_path)[0]
        if guessed:
            mime_type = guessed

        with open(image_path, 'rb') as f:
            files = {
                'input_file': (os.path.basename(image_path), f, mime_type)
            }
            response = self._session.post(url, files=files)

        if not response.ok:
            self._logger.error(f"Ошибка загрузки изображения {image_path}: {response.status_code}")
            raise RuntimeError("Upload failed")

        return response.json().get('id', 'unknown')
