import io
import os
import re
import urllib.request
from tempfile import NamedTemporaryFile

import cloudinary
import cloudinary.uploader


_CLOUDINARY_CONFIGURED = False


def _configure_cloudinary() -> None:
    global _CLOUDINARY_CONFIGURED
    if _CLOUDINARY_CONFIGURED:
        return

    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not cloud_name or not api_key or not api_secret:
        raise RuntimeError("Cloudinary não configurado. Defina CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY e CLOUDINARY_API_SECRET.")

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    _CLOUDINARY_CONFIGURED = True


def is_remote_asset(path_or_url: str | None) -> bool:
    return bool(path_or_url and str(path_or_url).startswith(("http://", "https://")))


def read_audio_bytes(path_or_url: str) -> bytes:
    if is_remote_asset(path_or_url):
        with urllib.request.urlopen(path_or_url, timeout=30) as resp:
            return resp.read()
    with open(path_or_url, "rb") as f:
        return f.read()


def upload_audio_bytes(audio_bytes: bytes, filename: str, folder: str) -> dict:
    _configure_cloudinary()
    result = cloudinary.uploader.upload(
        io.BytesIO(audio_bytes),
        resource_type="video",
        folder=folder,
        use_filename=True,
        unique_filename=True,
        filename_override=filename,
        overwrite=False,
    )
    return {
        "secure_url": result.get("secure_url"),
        "public_id": result.get("public_id"),
        "bytes": result.get("bytes", len(audio_bytes)),
        "format": result.get("format"),
    }


def extract_public_id_from_url(url: str | None) -> str | None:
    if not url or not is_remote_asset(url):
        return None
    # Ex: .../upload/v1710000000/folder/name.ext
    match = re.search(r"/upload/(?:v\d+/)?(.+?)(?:\.[a-zA-Z0-9]+)?(?:\?.*)?$", url)
    if not match:
        return None
    return match.group(1)


def delete_asset(path_or_url: str | None) -> None:
    if not path_or_url:
        return

    if not is_remote_asset(path_or_url):
        if os.path.exists(path_or_url):
            try:
                os.remove(path_or_url)
            except Exception:
                pass
        return

    public_id = extract_public_id_from_url(path_or_url)
    if not public_id:
        return

    try:
        _configure_cloudinary()
        cloudinary.uploader.destroy(public_id, resource_type="video", invalidate=True)
    except Exception:
        pass


def write_temp_audio_file(audio_bytes: bytes, suffix: str = ".wav") -> str:
    tmp = NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(audio_bytes)
        return tmp.name
    finally:
        tmp.close()
