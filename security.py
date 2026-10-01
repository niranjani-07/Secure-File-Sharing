from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    """Convert a plain password into a secure hash."""
    return generate_password_hash(password)


def verify_password(hashed_password, password):
    """Check whether the entered password matches the stored hash."""
    return check_password_hash(hashed_password, password)