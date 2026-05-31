import json
from json import JSONDecodeError
from pathlib import Path

from services.logging_service import logger


APPROVED_USERS_PATH = Path("config/approved_users.json")
APPROVED_USERS_EXAMPLE_PATH = Path("config/approved_users.example.json")


def _get_users_path() -> Path:
    logger.info("Checking approved users config paths.")

    if APPROVED_USERS_PATH.exists():
        logger.info(f"Using approved users file: {APPROVED_USERS_PATH}")
        return APPROVED_USERS_PATH

    logger.warning(
        f"{APPROVED_USERS_PATH} not found. Falling back to {APPROVED_USERS_EXAMPLE_PATH}."
    )
    return APPROVED_USERS_EXAMPLE_PATH


def load_approved_users() -> list[dict]:
    path = _get_users_path()

    if not path.exists():
        logger.error(f"No approved users file found at: {path}")
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

    except JSONDecodeError:
        logger.exception(f"Approved users file is not valid JSON: {path}")
        return []

    except Exception:
        logger.exception(f"Unexpected error loading approved users file: {path}")
        return []

    users = data.get("users", [])

    if not isinstance(users, list):
        logger.error("Approved users file does not contain a valid 'users' list.")
        return []

    logger.info(f"Loaded {len(users)} approved user records from {path}.")
    return users


def authenticate_user(email: str, access_code: str) -> dict | None:
    normalised_email = email.strip().lower()
    logger.info(f"Login attempt for email: {normalised_email}")

    if not normalised_email:
        logger.warning("Login failed: email was blank.")
        return None

    if not access_code:
        logger.warning(f"Login failed for {normalised_email}: access code was blank.")
        return None

    users = load_approved_users()

    if not users:
        logger.error("Login failed: no approved users loaded.")
        return None

    for user in users:
        user_email = user.get("email", "").strip().lower()
        user_id = user.get("user_id", "unknown_user")

        if user_email != normalised_email:
            continue

        logger.info(f"Found matching email for user_id={user_id}.")

        if not user.get("active", False):
            logger.warning(f"Login failed for {normalised_email}: user is inactive.")
            return None

        if user.get("access_code") != access_code:
            logger.warning(f"Login failed for {normalised_email}: access code mismatch.")
            return None

        role = user.get("role", "user")

        logger.info(
            f"Login successful for {normalised_email}; user_id={user_id}; role={role}."
        )

        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "display_name": user.get("display_name", user["email"]),
            "role": role,
        }

    logger.warning(f"Login failed: no user found for email {normalised_email}.")
    return None


def get_client_users() -> list[dict]:
    users = load_approved_users()
    clients = [
        user
        for user in users
        if user.get("role") == "user" and user.get("active", False)
    ]

    logger.info(f"Loaded {len(clients)} active client users.")
    return clients