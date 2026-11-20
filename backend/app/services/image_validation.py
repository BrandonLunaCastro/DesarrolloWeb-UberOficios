class ImageValidationError(ValueError):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
_IMAGE_SIGNATURES = {
    "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda data: (
        len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    ),
}


def validar_imagen(contenido: bytes, content_type: str | None, nombre: str) -> None:
    if len(contenido) > MAX_IMAGE_SIZE_BYTES:
        raise ImageValidationError(
            f"{nombre}: supera el límite de 5 MB.",
            status_code=413,
        )
    if not contenido:
        raise ImageValidationError(f"{nombre}: la imagen está vacía.")
    valida_firma = _IMAGE_SIGNATURES.get(content_type or "")
    if valida_firma is None or not valida_firma(contenido):
        raise ImageValidationError(
            f"{nombre}: solo se permiten imágenes JPG, PNG o WebP válidas."
        )
