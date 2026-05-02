import hashlib
import base64
import random


def hash_password_raw(password: str) -> str:
    hash_data = hashlib.sha256(password.encode("utf-8"))
    return base64.b64encode(hash_data.digest()).decode("utf-8")


def hash_password(password: str) -> str:
    salt = get_salt()
    return hash_password_raw(password + ":" + salt) + ":" + salt


def get_salt() -> str:
    salt_number = random.randint(0, 2 ** 256 - 1)
    return base64.b64encode(salt_number.to_bytes(32, "little")).decode("utf-8")


def passwords_equal(password: str, hash: str) -> bool:
    raw_hash, salt = hash.split(":", 2)
    return hash_password_raw(password + ":" + salt) == raw_hash
