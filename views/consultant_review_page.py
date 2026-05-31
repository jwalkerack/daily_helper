import streamlit as st

from services.auth_service import get_client_users
from services.azure_storage_service import load_latest_questionnaire_submission, load_user_status


def _display_answers(submission: dict):
    answers = submission.get("answers", {})

    if not answers:
        st.info("No answers found in this submission.")
        return

    for question_id, answer in answers.items():
        st.markdown(f"**{question_id}**")

        if isinstance(answer, list):
            if answer:
                for item in answer:
                    st.write(f"- {item}")
            else:
                st.caption("No selection")
        else:
            st.write(answer if answer else "No answer")

        st.divider()


def render_consultant_review_page():
    st.title("Consultant - User Review")

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

    st.subheader("User status")
    status = load_user_status(selected_user["user_id"])

    if status:
        st.json(status)
    else:
        st.info("No status file found for this user yet.")

    st.subheader("Latest questionnaire submission")
    submission = load_latest_questionnaire_submission(selected_user["user_id"])

    if not submission:
        st.info("No questionnaire submission found for this user yet.")
        return

    with st.expander("Raw submission JSON"):
        st.json(submission)

    st.subheader("Answers")
    _display_answers(submission)
