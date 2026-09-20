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


def upload_verification_doc(file_storage, user_id):
    """
    Upload a professional's verification document (ID, certificate, etc.)
    to Cloudinary as a PRIVATE asset — unlike avatars, this must not be a
    guessable public URL, since it's a photo of someone's identity
    document. Returns (public_id, format) — callers store both, since
    verification_doc_url() needs the format to build the right signed URL.
    """
    result = cloudinary.uploader.upload(
        file_storage,
        folder="quickfix/verification_docs",
        public_id=f"user_{user_id}",
        overwrite=True,
        resource_type="image",
        type="private",
    )
    return result["public_id"], result["format"]


def verification_doc_url(public_id, doc_format):
    """Generate a signed download URL for a verification doc that expires
    in 10 minutes — an admin reviewing the queue gets a working link, but
    it can't be bookmarked, shared, or scraped for permanent access."""
    import time

    return cloudinary.utils.private_download_url(
        public_id,
        doc_format,
        resource_type="image",
        type="private",
        expires_at=int(time.time()) + 600,
    )
