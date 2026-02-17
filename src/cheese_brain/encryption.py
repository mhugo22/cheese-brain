"""
Encryption utilities for backup files.
"""

import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

# File header for encrypted backups
ENCRYPTED_HEADER = b"CHEESE_BRAIN_ENCRYPTED_V1\n"


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive encryption key from passphrase using PBKDF2.
    
    Args:
        passphrase: User-provided passphrase
        salt: Random salt (16 bytes)
        
    Returns:
        32-byte encryption key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,  # OWASP recommendation (2023)
    )
    key = kdf.derive(passphrase.encode('utf-8'))
    return base64.urlsafe_b64encode(key)


def encrypt_file(input_path: str, output_path: str, passphrase: str) -> None:
    """Encrypt a file with a passphrase.
    
    Args:
        input_path: Path to plain text file
        output_path: Path to write encrypted file
        passphrase: Encryption passphrase
    """
    # Generate random salt
    salt = os.urandom(16)
    
    # Derive key from passphrase
    key = derive_key(passphrase, salt)
    fernet = Fernet(key)
    
    # Read plain text
    with open(input_path, 'rb') as f:
        plaintext = f.read()
    
    # Encrypt
    ciphertext = fernet.encrypt(plaintext)
    
    # Write encrypted file with header and salt
    with open(output_path, 'wb') as f:
        f.write(ENCRYPTED_HEADER)
        f.write(salt)
        f.write(ciphertext)
    
    # Secure permissions
    os.chmod(output_path, 0o600)


def decrypt_file(input_path: str, output_path: str, passphrase: str) -> None:
    """Decrypt a file with a passphrase.
    
    Args:
        input_path: Path to encrypted file
        output_path: Path to write decrypted file
        passphrase: Decryption passphrase
        
    Raises:
        ValueError: If file is not encrypted or passphrase is wrong
    """
    # Read encrypted file
    with open(input_path, 'rb') as f:
        data = f.read()
    
    # Check header
    if not data.startswith(ENCRYPTED_HEADER):
        raise ValueError("File is not an encrypted Cheese Brain backup")
    
    # Extract salt and ciphertext
    header_len = len(ENCRYPTED_HEADER)
    salt = data[header_len:header_len + 16]
    ciphertext = data[header_len + 16:]
    
    # Derive key from passphrase
    key = derive_key(passphrase, salt)
    fernet = Fernet(key)
    
    # Decrypt
    try:
        plaintext = fernet.decrypt(ciphertext)
    except Exception:
        raise ValueError("Decryption failed. Wrong passphrase?")
    
    # Write decrypted file
    with open(output_path, 'wb') as f:
        f.write(plaintext)
    
    # Secure permissions
    os.chmod(output_path, 0o600)


def is_encrypted(file_path: str) -> bool:
    """Check if a file is an encrypted backup.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file is encrypted
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(len(ENCRYPTED_HEADER))
        return header == ENCRYPTED_HEADER
    except Exception:
        return False
