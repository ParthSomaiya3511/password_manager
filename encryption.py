import base64
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.fernet import Fernet

def derive_key(pin: str) -> bytes:
    """Derives a cryptographically strong 32-byte key from the Master PIN."""
    salt = b"pm_fixed_salt_val_secure"
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
    )
    key = kdf.derive(pin.encode())
    return base64.urlsafe_b64encode(key)

def encrypt_password(password: str, pin: str) -> str:
    """Encrypts a string using the derived key."""
    key = derive_key(pin)
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str, pin: str) -> str:
    """Decrypts a string using the derived key."""
    try:
        key = derive_key(pin)
        f = Fernet(key)
        return f.decrypt(encrypted_password.encode()).decode()
    except Exception:
        return "[Decryption Error: Invalid PIN]"