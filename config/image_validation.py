"""Общая валидация загружаемых изображений (лимит размера, JPEG/PNG)."""

from django.core.exceptions import ValidationError

MAX_UPLOAD_IMAGE_BYTES = 5 * 1024 * 1024

_ALLOWED_IMAGE_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/jpg",
    }
)


def validate_uploaded_image_file(image) -> None:
    """
    Проверяет размер, Content-Type (если передан клиентом) и сигнатуру JPEG/PNG.
    После вызова указатель файла сбрасывается в начало.
    """
    if image.size > MAX_UPLOAD_IMAGE_BYTES:
        raise ValidationError("Размер файла не должен превышать 5 МБ.")
    content_type = getattr(image, "content_type", "") or ""
    if content_type and content_type not in _ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValidationError("Допустимы только изображения в формате JPEG или PNG.")
    head = image.read(12)
    image.seek(0)
    is_jpeg = head[:3] == b"\xff\xd8\xff"
    is_png = head[:8] == b"\x89PNG\r\n\x1a\n"
    if not (is_jpeg or is_png):
        raise ValidationError("Файл не является корректным изображением JPEG или PNG.")
