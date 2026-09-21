"""
Symmetric encryption for sensitive values stored in the database —
currently just the Paystack API keys (app/routes/admin.py's platform
settings screen).

The encryption key is derived from the app's SECRET_KEY via PBKDF2,
rather than requiring a separate secret to provision and keep safe.
The real tradeoff this creates: rotating SECRET_KEY makes every
previously-encrypted value undecryptable. That's an acceptable cost for
now (SECRET_KEY rotation isn't something this app does routinely, and a
compromised SECRET_KEY is already a session-forgery-level incident on
its own), but it means whoever changes SECRET_KEY in production needs to
re-enter the Paystack keys in /admin/settings afterward — noted in the
admin settings template too.
"""
import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Fixed salt is acceptable here: we're deriving one key from one secret
# for one purpose (not hashing many different user passwords, where a
# fixed salt would be a real problem). The salt's job is just to make
# this derived key distinct from SECRET_KEY's other uses (session
# signing, CSRF tokens), not to defend against rainbow tables.
_SALT = b"quickfix-nearby-platform-settings-v1"


def _fernet():
    secret_key = os.environ.get("SECRET_KEY", "")
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be set to encrypt/decrypt platform settings.")
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_SALT, iterations=480_000)
    derived = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return Fernet(derived)


def encrypt_value(plaintext):
    if not plaintext:
        return None
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext):
    """Returns None (not an exception) if ciphertext is empty or can't be
    decrypted with the current SECRET_KEY — callers treat that the same
    as "not configured" rather than crashing the page that needed it."""
    if not ciphertext:
        return None
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError):
        return None
