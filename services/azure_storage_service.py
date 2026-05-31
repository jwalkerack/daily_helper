import json
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from azure.core.exceptions import AzureError, ResourceNotFoundError, ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContentSettings

from services.logging_service import logger


load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        logger.error(f"Missing required environment variable: {name}")
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


def _get_container_client():
    connection_string = _get_required_env("AZURE_STORAGE_CONNECTION_STRING")
    container_name = _get_required_env("AZURE_STORAGE_CONTAINER_NAME")

    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )

        container_client = blob_service_client.get_container_client(container_name)

        return container_client

    except AzureError:
        logger.exception("Failed to create Azure container client.")
        raise

    except Exception:
        logger.exception("Unexpected error while creating Azure container client.")
        raise


def test_azure_connection() -> bool:
    """
    Simple diagnostic helper.
    Lists container properties to confirm the app can connect to Azure Blob Storage.
    """
    try:
        container_client = _get_container_client()
        properties = container_client.get_container_properties()

        logger.info(
            f"Azure connection test successful. Container: {container_client.container_name}"
        )
        logger.info(f"Container last modified: {properties.get('last_modified')}")

        return True

    except AzureError:
        logger.exception("Azure connection test failed.")
        return False

    except Exception:
        logger.exception("Unexpected error during Azure connection test.")
        return False


def _upload_json(blob_name: str, data: dict[str, Any]) -> str:
    try:
        container_client = _get_container_client()
        blob_client = container_client.get_blob_client(blob_name)

        json_text = json.dumps(data, indent=2, ensure_ascii=False)

        blob_client.upload_blob(
            json_text,
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json"),
        )

        logger.info(f"Uploaded JSON blob successfully: {blob_name}")

        return blob_name

    except AzureError:
        logger.exception(f"Azure error uploading JSON blob: {blob_name}")
        raise

    except Exception:
        logger.exception(f"Unexpected error uploading JSON blob: {blob_name}")
        raise


def _download_json(blob_name: str) -> dict | None:
    try:
        container_client = _get_container_client()
        blob_client = container_client.get_blob_client(blob_name)

        blob_data = blob_client.download_blob().readall()
        logger.info(f"Downloaded JSON blob successfully: {blob_name}")

        return json.loads(blob_data.decode("utf-8"))

    except ResourceNotFoundError:
        logger.info(f"JSON blob not found: {blob_name}")
        return None

    except AzureError:
        logger.exception(f"Azure error downloading JSON blob: {blob_name}")
        raise

    except json.JSONDecodeError:
        logger.exception(f"Blob contained invalid JSON: {blob_name}")
        raise

    except Exception:
        logger.exception(f"Unexpected error downloading JSON blob: {blob_name}")
        raise


def _list_blob_names(prefix: str) -> list[str]:
    try:
        container_client = _get_container_client()

        blob_names = [
            blob.name
            for blob in container_client.list_blobs(name_starts_with=prefix)
        ]

        logger.info(f"Listed {len(blob_names)} blobs with prefix: {prefix}")

        return blob_names

    except AzureError:
        logger.exception(f"Azure error listing blobs with prefix: {prefix}")
        raise

    except Exception:
        logger.exception(f"Unexpected error listing blobs with prefix: {prefix}")
        raise


def _user_root(user_id: str) -> str:
    return f"users/{user_id}"


def _status_blob_name(user_id: str) -> str:
    return f"{_user_root(user_id)}/status.json"


def _profile_blob_name(user_id: str) -> str:
    return f"{_user_root(user_id)}/profile/profile_v1.json"


def save_user_status(user_id: str, status: dict) -> str:
    logger.info(f"Saving user status for user_id={user_id}")
    return _upload_json(_status_blob_name(user_id), status)


def load_user_status(user_id: str) -> dict | None:
    logger.info(f"Loading user status for user_id={user_id}")
    return _download_json(_status_blob_name(user_id))


def save_questionnaire_submission(user: dict, questionnaire: dict, answers: dict) -> str:
    user_id = user["user_id"]

    logger.info(f"Saving questionnaire submission for user_id={user_id}")

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H%M%SZ")

    questionnaire_id = questionnaire["id"]
    questionnaire_version = questionnaire["version"]

    submission_blob_name = (
        f"{_user_root(user_id)}/questionnaire_submissions/"
        f"{questionnaire_id}_v{questionnaire_version}_{timestamp}.json"
    )

    submission_payload = {
        "user_id": user_id,
        "email": user["email"],
        "display_name": user.get("display_name"),
        "questionnaire_id": questionnaire_id,
        "questionnaire_version": questionnaire_version,
        "submitted_at": now.isoformat(),
        "answers": answers,
    }

    _upload_json(submission_blob_name, submission_payload)

    status = {
        "user_id": user_id,
        "email": user["email"],
        "display_name": user.get("display_name"),
        "account_status": "active",
        "questionnaire_status": "submitted",
        "profile_status": "not_started",
        "ai_helper_enabled": False,
        "last_questionnaire_submission_path": submission_blob_name,
        "updated_at": now.isoformat(),
    }

    save_user_status(user_id, status)

    logger.info(
        f"Questionnaire submission saved and status updated for user_id={user_id}"
    )

    return submission_blob_name


def load_latest_questionnaire_submission(user_id: str) -> dict | None:
    logger.info(f"Loading latest questionnaire submission for user_id={user_id}")

    prefix = f"{_user_root(user_id)}/questionnaire_submissions/"
    blob_names = _list_blob_names(prefix)

    json_blob_names = [
        blob_name
        for blob_name in blob_names
        if blob_name.endswith(".json")
    ]

    if not json_blob_names:
        logger.info(f"No questionnaire submissions found for user_id={user_id}")
        return None

    latest_blob_name = sorted(json_blob_names, reverse=True)[0]

    logger.info(
        f"Latest questionnaire submission for user_id={user_id}: {latest_blob_name}"
    )

    return _download_json(latest_blob_name)


def save_consultant_profile(
    selected_user: dict,
    consultant_user: dict,
    profile_text: str,
    profile_status: str,
) -> str:
    user_id = selected_user["user_id"]

    logger.info(
        f"Saving consultant profile for user_id={user_id}, profile_status={profile_status}"
    )

    now = datetime.now(timezone.utc)
    profile_blob_name = _profile_blob_name(user_id)

    profile_payload = {
        "user_id": user_id,
        "email": selected_user["email"],
        "display_name": selected_user.get("display_name"),
        "profile_version": 1,
        "profile_status": profile_status,
        "created_or_updated_by": consultant_user["user_id"],
        "updated_at": now.isoformat(),
        "profile_text": profile_text,
    }

    _upload_json(profile_blob_name, profile_payload)

    existing_status = load_user_status(user_id) or {
        "user_id": user_id,
        "email": selected_user["email"],
        "display_name": selected_user.get("display_name"),
        "account_status": "active",
        "questionnaire_status": "not_started",
    }

    existing_status.update(
        {
            "profile_status": profile_status,
            "ai_helper_enabled": profile_status == "ready",
            "active_profile_path": profile_blob_name,
            "updated_at": now.isoformat(),
        }
    )

    save_user_status(user_id, existing_status)

    logger.info(f"Consultant profile saved for user_id={user_id}")

    return profile_blob_name


def load_consultant_profile(user_id: str) -> dict | None:
    logger.info(f"Loading consultant profile for user_id={user_id}")
    return _download_json(_profile_blob_name(user_id))


def list_all_blob_names(prefix: str = "") -> list[str]:
    """
    Lists file-like blob names in the configured Azure Storage container.

    Skips ADLS directory markers so the admin preview/delete tool only targets
    actual stored files such as status.json, profile_v1.json, and submissions.
    """
    try:
        container_client = _get_container_client()

        blob_names = []

        for blob in container_client.list_blobs(name_starts_with=prefix):
            blob_name = blob.name

            # ADLS / hierarchical namespace accounts can expose directory markers.
            # We only want to target actual files.
            if blob_name.endswith("/"):
                logger.info(f"Skipping directory marker in preview: {blob_name}")
                continue

            blob_names.append(blob_name)

        logger.info(f"Listed {len(blob_names)} file blobs with prefix: {prefix}")

        return blob_names

    except AzureError:
        logger.exception(f"Azure error listing blobs with prefix: {prefix}")
        raise

    except Exception:
        logger.exception(f"Unexpected error listing blobs with prefix: {prefix}")
        raise


def delete_blobs_by_prefix(prefix: str = "users/") -> int:
    """
    Deletes file blobs from the configured Azure Storage container by prefix.

    This intentionally skips ADLS directory markers. Deleting the actual JSON/file
    blobs is enough to reset the app, because the app checks for files such as:
    - users/{user_id}/status.json
    - users/{user_id}/questionnaire_submissions/*.json
    - users/{user_id}/profile/profile_v1.json
    """
    try:
        container_client = _get_container_client()
        blob_names = list_all_blob_names(prefix=prefix)

        if not blob_names:
            logger.info(f"No file blobs found to delete with prefix: {prefix}")
            return 0

        deleted_count = 0
        skipped_count = 0

        # Delete deepest paths first. This helps with ADLS-style hierarchical storage.
        blob_names = sorted(blob_names, key=lambda name: name.count("/"), reverse=True)

        for blob_name in blob_names:
            if blob_name.endswith("/"):
                skipped_count += 1
                logger.info(f"Skipping directory marker during delete: {blob_name}")
                continue

            try:
                blob_client = container_client.get_blob_client(blob_name)
                blob_client.delete_blob()
                deleted_count += 1
                logger.info(f"Deleted blob: {blob_name}")

            except ResourceNotFoundError:
                skipped_count += 1
                logger.warning(f"Blob already missing during delete: {blob_name}")

            except ResourceExistsError as error:
                skipped_count += 1
                logger.warning(
                    f"Skipped non-empty ADLS directory during delete: {blob_name}. "
                    f"Azure error: {error}"
                )

        logger.warning(
            f"Admin delete complete for prefix={prefix}. "
            f"Deleted={deleted_count}, skipped={skipped_count}"
        )

        return deleted_count

    except AzureError:
        logger.exception(f"Azure error deleting blobs with prefix: {prefix}")
        raise

    except Exception:
        logger.exception(f"Unexpected error deleting blobs with prefix: {prefix}")
        raise