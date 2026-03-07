import hashlib
import secrets
import sys


def hash_password(password: str):
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256()
    hash_obj.update(f"{salt}{password}".encode())
    return f"sha256:{salt}:{hash_obj.hexdigest()}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/generate_hash.py <password>")
        sys.exit(1)

    password = sys.argv[1]
    hashed = hash_password(password)
    print(f"\nPassword: {password}")
    print(f"Hashed: {hashed}")
    print("\nPlease copy the 'Hashed' value to your .env file as ADMIN_PASSWORD_HASH.\n")
