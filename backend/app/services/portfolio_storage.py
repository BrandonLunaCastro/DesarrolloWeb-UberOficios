import io
import os

import cloudinary
from cloudinary import uploader
from cloudinary.exceptions import Error as CloudinaryError


class CloudinaryNotConfiguredError(Exception):
    pass


def _configure_cloudinary() -> None:
    credentials = {
        "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "api_key": os.getenv("CLOUDINARY_API_KEY"),
        "api_secret": os.getenv("CLOUDINARY_API_SECRET"),
    }
    if not all(credentials.values()):
        raise CloudinaryNotConfiguredError

    cloudinary.config(**credentials, secure=True)


def upload_portfolio_image(content: bytes, folder: str) -> dict:
    _configure_cloudinary()
    return uploader.upload(
        io.BytesIO(content),
        folder=folder,
        resource_type="image",
        allowed_formats=["jpg", "jpeg", "png", "webp"],
        unique_filename=True,
        overwrite=False,
    )


def delete_portfolio_image(public_id: str) -> dict:
    _configure_cloudinary()
    return uploader.destroy(
        public_id,
        resource_type="image",
        invalidate=True,
    )


__all__ = [
    "CloudinaryError",
    "CloudinaryNotConfiguredError",
    "delete_portfolio_image",
    "upload_portfolio_image",
]
