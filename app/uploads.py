import os

import cloudinary
import cloudinary.uploader


def cloudinary_configured():
    """True once all three Cloudinary env vars are present."""
    return bool(
        os.environ.get("CLOUDINARY_CLOUD_NAME")
        and os.environ.get("CLOUDINARY_API_KEY")
        and os.environ.get("CLOUDINARY_API_SECRET")
    )


def init_cloudinary(app):
    """Configure the Cloudinary SDK once at app startup, if credentials exist."""
    if cloudinary_configured():
        cloudinary.config(
            cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
            api_key=os.environ["CLOUDINARY_API_KEY"],
            api_secret=os.environ["CLOUDINARY_API_SECRET"],
            secure=True,
        )
    else:
        app.logger.warning(
            "Cloudinary env vars not set — avatar uploads will show a friendly error until configured."
        )


def upload_avatar(file_storage, user_id):
    """
    Upload a profile photo to Cloudinary, replacing any previous one for this user.
    Returns the new secure_url. Raises on failure — callers should catch and flash.
    """
    result = cloudinary.uploader.upload(
        file_storage,
        folder="quickfix/avatars",
        public_id=f"user_{user_id}",
        overwrite=True,
        resource_type="image",
        transformation=[{"width": 400, "height": 400, "crop": "fill", "gravity": "face"}],
    )
    return result["secure_url"]
