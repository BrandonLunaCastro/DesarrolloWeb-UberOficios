import unittest

from app.services.image_validation import (
    MAX_IMAGE_SIZE_BYTES,
    ImageValidationError,
    validar_imagen,
)


class ValidarImagenTests(unittest.TestCase):
    def test_acepta_firmas_validas_jpg_png_y_webp(self):
        imagenes = (
            ("image/jpeg", b"\xff\xd8\xff"),
            ("image/png", b"\x89PNG\r\n\x1a\n"),
            ("image/webp", b"RIFF\x00\x00\x00\x00WEBP"),
        )

        for content_type, contenido in imagenes:
            with self.subTest(content_type=content_type):
                validar_imagen(contenido, content_type, "Comprobante")

    def test_rechaza_tipo_y_firma_incompatibles(self):
        with self.assertRaises(ImageValidationError):
            validar_imagen(b"\x89PNG\r\n\x1a\n", "image/jpeg", "Comprobante")

    def test_rechaza_archivos_mayores_a_5_mb(self):
        with self.assertRaises(ImageValidationError) as context:
            validar_imagen(
                b"x" * (MAX_IMAGE_SIZE_BYTES + 1),
                "image/jpeg",
                "Comprobante",
            )

        self.assertEqual(context.exception.status_code, 413)


if __name__ == "__main__":
    unittest.main()
