import streamlit as st

from services.ai_service import get_ai_response
from services.azure_storage_service import load_consultant_profile, load_user_status
from services.logging_service import logger


def _build_session_download(messages: list[dict]) -> str:
    output = "# Daily Helper AI Session\n\n"

    for message in messages:
        role = "You" if message["role"] == "user" else "AI Helper"
        output += f"## {role}\n\n{message['content']}\n\n"

    return output


def _initialise_chat_state(user_id: str):
    """
    Keeps each user's chat separate in Streamlit session state.
    """

    chat_key = f"chat_messages_{user_id}"

    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    return chat_key


def _show_not_ready_message(status: dict | None):
    st.title("AI Helper")

    if not status:
        st.info(
            "Your AI helper is not ready yet. "
            "Please complete your questionnaire first."
        )
        return

    questionnaire_status = status.get("questionnaire_status")
    profile_status = status.get("profile_status")
    ai_helper_enabled = status.get("ai_helper_enabled", False)

    if questionnaire_status != "submitted":
        st.info(
            "Your AI helper is not ready yet. "
            "Please complete your questionnaire first."
        )
        return

    if profile_status != "ready" or not ai_helper_enabled:
        st.info(
            "Your AI helper is not ready yet. "
            "Your consultant is preparing your review."
        )
        return


def _user_can_access_ai_helper(status: dict | None) -> bool:
    if not status:
        return False

    return (
        status.get("questionnaire_status") == "submitted"
        and status.get("profile_status") == "ready"
        and status.get("ai_helper_enabled") is True
    )


def render_ai_chat_page():
    st.title("AI Helper")

    user = st.session_state.get("user")

    if not user:
        st.error("You must be logged in to use the AI helper.")
        logger.warning("AI Helper accessed without logged-in user.")
        return

    user_id = user["user_id"]

    status = load_user_status(user_id)

    if not _user_can_access_ai_helper(status):
        _show_not_ready_message(status)
        return

    profile = load_consultant_profile(user_id)

    if not profile:
        st.warning(
            "Your AI helper has been enabled, but your consultant review could not be found. "
            "Please contact your consultant."
        )
        logger.warning(f"AI Helper enabled but no profile found for user_id={user_id}")
        return

    profile_text = profile.get("profile_text", "").strip()

    if not profile_text:
        st.warning(
            "Your AI helper has been enabled, but your consultant review is empty. "
            "Please contact your consultant."
        )
        logger.warning(f"AI Helper enabled but profile text is empty for user_id={user_id}")
        return

    chat_key = _initialise_chat_state(user_id)

    with st.expander("About your AI helper", expanded=True):
        st.write(
            "This AI helper uses the review prepared by your consultant to provide "
            "personalised reflective support."
        )
        st.write(
            "It is not a therapist, doctor, emergency service, or crisis service. "
            "If you are in immediate danger or need urgent help, contact emergency "
            "services or a crisis support service."
        )

    if not st.session_state[chat_key]:
        st.chat_message("assistant").write(
            "Hi, I’m your Daily Helper. I can help you reflect on things using the "
            "review your consultant has prepared. What would you like to talk about?"
        )

    for message in st.session_state[chat_key]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_message = st.chat_input("Write your message")

    if user_message:
        st.session_state[chat_key].append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        with st.chat_message("user"):
            st.write(user_message)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response = get_ai_response(
                    profile_text=profile_text,
                    messages=st.session_state[chat_key],
                    user_message=user_message,
                )

            st.write(ai_response)

        st.session_state[chat_key].append(
            {
                "role": "assistant",
                "content": ai_response,
            }
        )

    if st.session_state[chat_key]:
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="Download this chat session",
                data=_build_session_download(st.session_state[chat_key]),
                file_name="daily_helper_ai_session.md",
                mime="text/markdown",
            )

        with col2:
            if st.button("Clear this chat"):
                st.session_state[chat_key] = []
                st.rerun()