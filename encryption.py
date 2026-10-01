import os
from cryptography.fernet import Fernet

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

KEY_FILE = os.path.join(BASE_DIR, "encryption.key")


def load_key():
    """
    Load the encryption key.
    If the key doesn't exist, create a new one.
    """

    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()

        with open(KEY_FILE, "wb") as file:
            file.write(key)

    else:
        with open(KEY_FILE, "rb") as file:
            key = file.read()

    return key


cipher = Fernet(load_key())


def encrypt_file(input_path, output_path):
    """
    Encrypt a file and save the encrypted version.
    """

    with open(input_path, "rb") as file:
        data = file.read()

    encrypted_data = cipher.encrypt(data)

    with open(output_path, "wb") as file:
        file.write(encrypted_data)


def decrypt_file(input_path, output_path):
    """
    Decrypt an encrypted file and save the original version.
    """

    with open(input_path, "rb") as file:
        encrypted_data = file.read()

    decrypted_data = cipher.decrypt(encrypted_data)

    with open(output_path, "wb") as file:
        file.write(decrypted_data)


def encrypt_data(data):
    """
    Encrypt raw data.
    """

    return cipher.encrypt(data)


def decrypt_data(data):
    """
    Decrypt encrypted data.
    """

    return cipher.decrypt(data)