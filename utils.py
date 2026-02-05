import re
import unicodedata
from typing import Tuple

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
EMAIL_MAX_LENGTH = 254

FULL_NAME_MIN_LENGTH = 2
FULL_NAME_MAX_LENGTH = 100

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 32

# unicode-aware username
# - letters, numbers
# - allows . _ -
# - no consecutive separators
# - must start/end with alphanumeric
USERNAME_REGEX = re.compile(r"^(?=.{3,30}$)[\w]+([._-][\w]+)*$", re.UNICODE)

EMAIL_REGEX = re.compile(
    r"^(?=.{1,254}$)" r"[A-Z0-9._%+-]+" r"@" r"(?:[A-Z0-9-]+\.)+[A-Z]{2,63}$",
    re.IGNORECASE,
)


def validate_username(username: str) -> Tuple[bool, str]:
    if not username:
        return False, "Username is required."

    username = username.strip()

    if not (USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH):
        return (
            False,
            f"Username must be between {USERNAME_MIN_LENGTH} and {USERNAME_MAX_LENGTH} characters.",
        )

    if not USERNAME_REGEX.match(username):
        return (
            False,
            "Username may contain letters, numbers, dots, underscores, and hyphens. "
            "It cannot start or end with a symbol.",
        )

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    if not email:
        return False, "Email is required."

    email = email.strip()

    if len(email) > EMAIL_MAX_LENGTH:
        return False, f"Email must be {EMAIL_MAX_LENGTH} characters or less."

    if not EMAIL_REGEX.match(email):
        return False, "Invalid email address."

    return True, ""


def validate_full_name(full_name: str) -> Tuple[bool, str]:
    if not full_name:
        return False, "Full name is required."

    full_name = full_name.strip()

    if not (FULL_NAME_MIN_LENGTH <= len(full_name) <= FULL_NAME_MAX_LENGTH):
        return (
            False,
            f"Full name must be between {FULL_NAME_MIN_LENGTH} and {FULL_NAME_MAX_LENGTH} characters.",
        )

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    if not password:
        return False, "Password is required."

    if len(password) < PASSWORD_MIN_LENGTH:
        return (
            False,
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters long.",
        )

    if len(password) > PASSWORD_MAX_LENGTH:
        return (
            False,
            f"Maximum password length allowed is {PASSWORD_MAX_LENGTH} characters.",
        )

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."

    return True, ""


def validate_bio(bio: str) -> Tuple[bool, str]:
    if bio is None:
        return True, ""

    if len(bio) > 500:
        return False, "Bio must be 500 characters or less."

    return True, ""


def generate_slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
