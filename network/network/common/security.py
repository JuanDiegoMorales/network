import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_symmetric_key() -> bytes:
    return AESGCM.generate_key(bit_length=128)


def encrypt_message(message: str, key: bytes) -> str:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    encrypted = aesgcm.encrypt(nonce, message.encode('utf-8'), None)
    return base64.b64encode(nonce + encrypted).decode('utf-8')


def decrypt_message(encrypted_message: str, key: bytes) -> str:
    encrypted_message = base64.b64decode(encrypted_message)
    nonce = encrypted_message[:12]
    ciphertext = encrypted_message[12:]
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted.decode('utf-8')


def encrypt_file(file_data: bytes, key: bytes) -> str:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    encrypted = aesgcm.encrypt(nonce, file_data, None)
    return base64.b64encode(nonce + encrypted).decode('utf-8')


def decrypt_file(encrypted_file: str, key: bytes) -> bytes:
    encrypted_file = base64.b64decode(encrypted_file)
    nonce = encrypted_file[:12]
    ciphertext = encrypted_file[12:]
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted


def generate_keys() -> (RSAPrivateKey, RSAPublicKey):
    private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key: RSAPublicKey = private_key.public_key()
    return private_key, public_key


def serialize_key_private(key: RSAPrivateKey) -> bytes:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )


def serialize_key_public(key: RSAPublicKey) -> str:
    pem = key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')


def deserialize_key_public(key_str: str) -> RSAPublicKey:
    return serialization.load_pem_public_key(key_str.encode('utf-8'), backend=default_backend())


def encrypt_symmetric_key(sym_key, public_key_str):
    public_key = deserialize_key_public(public_key_str)
    encrypted_key = public_key.encrypt(
        sym_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted_key).decode()


def decrypt_symmetric_key(enc_sym_key, private_key):
    enc_sym_key = base64.b64decode(enc_sym_key.encode())
    sym_key = private_key.decrypt(
        enc_sym_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return sym_key