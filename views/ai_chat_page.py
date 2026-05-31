import streamlit as st

from services.ai_service import get_ai_response
from services.azure_storage_service import load_consultant_profile, load_user_status


def _build_session_download(messages: list[dict]) -> str:
    output = "# Daily Helper AI Session\n\n"

    for message in messages:
        role = "You" if message["role"] == "user" else "AI Helper"
        output += f"## {role}\n\n{message['content']}\n\n"

    return output


def render_ai_chat_page():
    st.title("AI Helper")

    user = st.session_state["user"]
    status = load_user_status(user["user_id"])

    if not status:
        st.info("Your AI helper is not ready yet. Please complete your questionnaire first.")
        return

    if status.get("profile_status") != "ready" or not status.get("ai_helper_enabled"):
        st.info("Your AI helper is not ready yet. Your consultant is preparing your profile.")
        return

    profile = load_consultant_profile(user["user_id"])

    if not profile:
        st.warning("Profile status is ready, but no profile file was found.")
        return

    profile_text = profile.get("profile_text", "")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    with st.expander("AI helper notice", expanded=True):
        st.write(
            "This AI helper is for reflection and support. "
            "It is not a therapist, doctor, emergency service, or crisis service."
        )

    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_message = st.chat_input("Write your message")

    if user_message:
        st.session_state["chat_messages"].append({"role": "user", "content": user_message})

        with st.chat_message("user"):
            st.write(user_message)

        ai_response = get_ai_response(
            profile_text=profile_text,
            messages=st.session_state["chat_messages"],
            user_message=user_message,
        )

        st.session_state["chat_messages"].append({"role": "assistant", "content": ai_response})

        with st.chat_message("assistant"):
            st.write(ai_response)

    if st.session_state["chat_messages"]:
        st.download_button(
            label="Download this chat session",
            data=_build_session_download(st.session_state["chat_messages"]),
            file_name="daily_helper_ai_session.md",
            mime="text/markdown",
        )

        with st.expander("Debug: profile loaded into AI"):
            st.json(profile)
