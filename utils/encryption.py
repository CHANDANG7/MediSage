from cryptography.fernet import Fernet
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class DataEncryption:
    def __init__(self, password=None):
        if password is None:
            password = os.getenv('SECRET_KEY', 'default-secret-key-change-this')
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'medisage-salt-2024',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Encrypt string data"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt(self, encrypted_data):
        """Decrypt data"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()
    
    def encrypt_dict(self, data_dict):
        """Encrypt dictionary values"""
        encrypted = {}
        for key, value in data_dict.items():
            if value is not None:
                encrypted[key] = self.encrypt(str(value))
        return encrypted
    
    def decrypt_dict(self, encrypted_dict):
        """Decrypt dictionary values"""
        decrypted = {}
        for key, value in encrypted_dict.items():
            if value is not None:
                try:
                    decrypted[key] = self.decrypt(value)
                except:
                    decrypted[key] = value
        return decrypted
