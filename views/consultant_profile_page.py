import streamlit as st

from services.auth_service import get_client_users
from services.azure_storage_service import (
    load_consultant_profile,
    load_latest_questionnaire_submission,
    save_consultant_profile,
)


def render_consultant_profile_page():
    st.title("Consultant - Profile Builder")

    consultant_user = st.session_state["user"]
    clients = get_client_users()

    if not clients:
        st.warning("No client users found.")
        return

    client_lookup = {
        f"{client.get('display_name', client['email'])} ({client['email']})": client
        for client in clients
    }

    selected_label = st.selectbox("Select user", options=list(client_lookup.keys()))
    selected_user = client_lookup[selected_label]

    submission = load_latest_questionnaire_submission(selected_user["user_id"])

    if submission:
        with st.expander("View latest questionnaire submission"):
            st.json(submission)
    else:
        st.info("No questionnaire submission found for this user yet.")

    existing_profile = load_consultant_profile(selected_user["user_id"])
    existing_profile_text = existing_profile.get("profile_text", "") if existing_profile else ""

    st.subheader("Consultant overview / profile")

    profile_text = st.text_area(
        "Write the profile that will later be loaded into the AI helper",
        value=existing_profile_text,
        height=350,
        placeholder=(
            "Example: This client prefers a calm, structured and practical style. "
            "They may struggle with pressure and switching off..."
        ),
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Save draft"):
            path = save_consultant_profile(
                selected_user=selected_user,
                consultant_user=consultant_user,
                profile_text=profile_text,
                profile_status="draft",
            )
            st.success("Draft profile saved.")
            st.caption(f"Temporary local save path: {path}")

    with col2:
        if st.button("Mark profile ready", type="primary"):
            if not profile_text.strip():
                st.error("Please write a profile before marking it ready.")
                return

            path = save_consultant_profile(
                selected_user=selected_user,
                consultant_user=consultant_user,
                profile_text=profile_text,
                profile_status="ready",
            )
            st.success("Profile marked as ready. AI helper can now be enabled for this user.")
            st.caption(f"Temporary local save path: {path}")
