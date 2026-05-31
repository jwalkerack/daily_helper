import streamlit as st

from services.azure_storage_service import delete_blobs_by_prefix, list_all_blob_names
from services.logging_service import logger


RESET_CONFIRMATION_TEXT = "DELETE USER DATA"


def render_admin_page():
    st.title("Admin")

    user = st.session_state.get("user")

    if not user or user.get("role") != "admin":
        st.error("You do not have permission to access this page.")
        logger.warning("Non-admin user attempted to access admin page.")
        return

    st.warning(
        "This page contains destructive admin tools. "
        "Use only for development/testing."
    )

    st.subheader("Azure Storage reset")

    st.write(
        "This will delete all blobs under `users/` in the configured Azure Storage "
        "container. It will remove questionnaire submissions, user status files, "
        "and consultant profiles."
    )

    st.info(
        "After this reset, users will be able to submit questionnaires again because "
        "their previous `status.json` files will no longer exist."
    )

    with st.expander("Preview blobs that would be deleted"):
        if st.button("Load blob preview"):
            blob_names = list_all_blob_names(prefix="users/")

            if not blob_names:
                st.success("No user data blobs found.")
            else:
                st.write(f"{len(blob_names)} blobs found under `users/`.")
                st.dataframe(
                    [{"blob_name": blob_name} for blob_name in blob_names],
                    use_container_width=True,
                )

    st.divider()

    confirmation = st.text_input(
        f"Type {RESET_CONFIRMATION_TEXT} to confirm reset",
        placeholder=RESET_CONFIRMATION_TEXT,
    )

    reset_clicked = st.button(
        "Delete all user data from Azure Storage",
        type="primary",
        disabled=confirmation != RESET_CONFIRMATION_TEXT,
    )

    if reset_clicked:
        logger.warning(
            f"Admin reset triggered by user_id={user.get('user_id')}, "
            f"email={user.get('email')}"
        )

        deleted_count = delete_blobs_by_prefix(prefix="users/")

        st.success(f"Reset complete. Deleted {deleted_count} blobs under `users/`.")
        st.info("Users can now submit questionnaires again.")