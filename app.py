import json
from pathlib import Path

import streamlit as st


QUESTIONNAIRE_PATH = Path("questionnaires/user_form.json")


def load_questionnaire(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def render_question(question: dict):
    question_id = question["id"]
    label = question["label"]
    question_type = question["type"]
    required = question.get("required", False)
    placeholder = question.get("placeholder", "")
    help_text = question.get("help", None)

    display_label = f"{label} *" if required else label

    if question_type == "short_text":
        return st.text_input(
            display_label,
            key=question_id,
            placeholder=placeholder,
            help=help_text,
        )

    if question_type == "email":
        return st.text_input(
            display_label,
            key=question_id,
            placeholder=placeholder,
            help=help_text,
        )

    if question_type == "long_text":
        return st.text_area(
            display_label,
            key=question_id,
            placeholder=placeholder,
            help=help_text,
        )

    if question_type == "single_select":
        options = question.get("options", [])
        return st.selectbox(
            display_label,
            options=[""] + options,
            key=question_id,
            help=help_text,
        )

    if question_type == "multi_select":
        options = question.get("options", [])
        return st.multiselect(
            display_label,
            options=options,
            key=question_id,
            help=help_text,
        )

    if question_type == "scale":
        return st.slider(
            display_label,
            min_value=question.get("min", 1),
            max_value=question.get("max", 10),
            value=question.get("default", question.get("min", 1)),
            key=question_id,
            help=help_text,
        )

    if question_type == "checkbox":
        return st.checkbox(
            display_label,
            key=question_id,
            help=help_text,
        )

    if question_type == "yes_no":
        return st.radio(
            display_label,
            options=["", "Yes", "No"],
            key=question_id,
            horizontal=True,
            help=help_text,
        )

    st.warning(f"Unsupported question type: {question_type}")
    return None


def render_questionnaire(questionnaire: dict) -> dict:
    st.title(questionnaire.get("title", "Questionnaire"))

    if questionnaire.get("description"):
        st.write(questionnaire["description"])

    st.divider()

    answers = {}

    for section in questionnaire.get("sections", []):
        st.header(section["title"])

        if section.get("description"):
            st.caption(section["description"])

        for question in section.get("questions", []):
            answers[question["id"]] = render_question(question)

        st.divider()

    return answers


def validate_answers(questionnaire: dict, answers: dict) -> list[str]:
    errors = []

    for section in questionnaire.get("sections", []):
        for question in section.get("questions", []):
            if not question.get("required", False):
                continue

            question_id = question["id"]
            question_type = question["type"]
            answer = answers.get(question_id)

            if question_type in ["short_text", "email", "long_text", "single_select", "yes_no"]:
                if not answer or str(answer).strip() == "":
                    errors.append(question["label"])

            elif question_type == "multi_select":
                if not answer:
                    errors.append(question["label"])

            elif question_type == "checkbox":
                if answer is not True:
                    errors.append(question["label"])

            elif question_type == "scale":
                if answer is None:
                    errors.append(question["label"])

    return errors


def main():
    st.set_page_config(
        page_title="Questionnaire Preview",
        page_icon="🧠",
        layout="centered",
    )

    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)

    with st.sidebar:
        st.subheader("Preview mode")
        st.write("This page renders the questionnaire directly from JSON.")
        st.write(f"Questionnaire ID: `{questionnaire.get('id')}`")
        st.write(f"Version: `{questionnaire.get('version')}`")

    answers = render_questionnaire(questionnaire)

    submitted = st.button("Submit questionnaire", type="primary")

    if submitted:
        errors = validate_answers(questionnaire, answers)

        if errors:
            st.error("Please complete the required questions before submitting.")
            for error in errors:
                st.write(f"- {error}")
        else:
            submission = {
                "questionnaire_id": questionnaire["id"],
                "questionnaire_version": questionnaire["version"],
                "answers": answers,
            }

            st.success("Questionnaire submitted successfully.")

            st.subheader("Submission preview")
            st.json(submission)

            st.download_button(
                label="Download submission as JSON",
                data=json.dumps(submission, indent=2, ensure_ascii=False),
                file_name="questionnaire_submission.json",
                mime="application/json",
            )


if __name__ == "__main__":
    main()