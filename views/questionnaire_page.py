import json

import streamlit as st

from services.azure_storage_service import load_user_status, save_questionnaire_submission
from services.questionnaire_service import load_questionnaire, render_questionnaire, validate_answers


def render_questionnaire_page():
    user = st.session_state["user"]
    status = load_user_status(user["user_id"])

    if status and status.get("questionnaire_status") == "submitted":
        st.title("Questionnaire")
        st.success("Your questionnaire has already been submitted.")
        st.write("Your consultant will review your responses.")

        with st.expander("Status details"):
            st.json(status)

        return

    questionnaire = load_questionnaire()
    answers = render_questionnaire(questionnaire)

    submitted = st.button("Submit questionnaire", type="primary")

    if submitted:
        errors = validate_answers(questionnaire, answers)

        if errors:
            st.error("Please complete the required questions before submitting.")
            for error in errors:
                st.write(f"- {error}")
            return

        submission_path = save_questionnaire_submission(
            user=user,
            questionnaire=questionnaire,
            answers=answers,
        )

        submission = {
            "questionnaire_id": questionnaire["id"],
            "questionnaire_version": questionnaire["version"],
            "answers": answers,
        }

        st.success("Questionnaire submitted successfully.")
        st.write("Your consultant will review your responses.")

        with st.expander("Submission preview"):
            st.json(submission)

        st.download_button(
            label="Download submission as JSON",
            data=json.dumps(submission, indent=2, ensure_ascii=False),
            file_name="questionnaire_submission.json",
            mime="application/json",
        )

        st.caption(f"Temporary local save path: {submission_path}")
