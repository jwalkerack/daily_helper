import streamlit as st

from views.login_page import render_login_page
from views.questionnaire_page import render_questionnaire_page
from views.consultant_review_page import render_consultant_review_page
from views.consultant_profile_page import render_consultant_profile_page
from views.ai_chat_page import render_ai_chat_page
from services.logging_service import logger


def initialise_session_state():
    if "user" not in st.session_state:
        st.session_state["user"] = None

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Questionnaire"


def logout():
    logger.info("User clicked logout.")
    st.session_state.clear()
    st.rerun()


def get_navigation_options(role: str) -> list[str]:
    if role == "user":
        return ["Questionnaire", "AI Helper"]

    if role == "consultant":
        return ["User Review", "Profile Builder"]

    if role == "admin":
        return ["User Review", "Profile Builder", "Admin"]

    logger.warning(f"Unknown role provided for navigation: {role}")
    return []


def render_sidebar():
    user = st.session_state.get("user")

    with st.sidebar:
        st.title("Daily Helper")

        if not user:
            st.info("Please log in to continue.")
            return None

        st.write(f"Logged in as: **{user.get('display_name', user.get('email'))}**")
        st.caption(f"Role: {user.get('role')}")

        navigation_options = get_navigation_options(user.get("role"))

        selected_page = st.radio(
            "Navigation",
            options=navigation_options,
            key="current_page",
        )

        logger.info(f"Current selected page: {selected_page}")

        st.divider()

        if st.button("Log out"):
            logout()

    return selected_page


def main():
    st.set_page_config(
        page_title="Daily Helper",
        page_icon="🧠",
        layout="centered",
    )

    logger.info("App started / rerun triggered.")

    initialise_session_state()

    if not st.session_state.get("user"):
        logger.info("No logged-in user found. Showing login page.")
        render_login_page()
        return

    logger.info(f"Logged-in user found: {st.session_state.get('user')}")

    selected_page = render_sidebar()

    if selected_page == "Questionnaire":
        render_questionnaire_page()

    elif selected_page == "User Review":
        render_consultant_review_page()

    elif selected_page == "Profile Builder":
        render_consultant_profile_page()

    elif selected_page == "AI Helper":
        render_ai_chat_page()

    elif selected_page == "Admin":
        st.title("Admin")
        st.info("Admin tools will be added later.")

    else:
        logger.warning(f"No valid page selected: {selected_page}")
        st.warning("No page selected.")


if __name__ == "__main__":
    main()