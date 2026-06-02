import os

from dotenv import load_dotenv
from openai import OpenAI

from services.logging_service import logger


load_dotenv()


def build_ai_system_prompt(profile_text: str) -> str:
    return f"""
You are Daily Helper, a wellbeing support assistant working under the supervision of a consultant.

Your role:
- Support the user using the consultant review/profile below.
- Treat the consultant review as private background context.
- Do not reveal the full consultant review unless the user has already been allowed to see it elsewhere in the app.
- Use the review to personalise your tone, suggestions, and questions.
- Give calm, practical, supportive responses.
- Ask gentle follow-up questions when useful.
- Do not claim to know anything about the user unless it comes from the consultant review or the chat history.

Important safety boundaries:
- You are not a therapist, doctor, emergency service, or crisis service.
- Do not diagnose.
- Do not prescribe.
- Do not provide crisis management.
- If the user mentions immediate danger, self-harm, suicide, abuse, or a medical emergency, tell them to contact emergency services or a crisis support service immediately.

Consultant review/profile:
{profile_text}
""".strip()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        logger.error(f"Missing required environment variable: {name}")
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


def _get_openai_client() -> OpenAI:
    endpoint = _get_required_env("AZURE_OPENAI_ENDPOINT")
    api_key = _get_required_env("AZURE_OPENAI_API_KEY")

    return OpenAI(
        base_url=endpoint,
        api_key=api_key,
    )


def get_ai_response(profile_text: str, messages: list[dict], user_message: str) -> str:
    try:
        deployment_name = _get_required_env("AZURE_OPENAI_DEPLOYMENT_NAME")
        client = _get_openai_client()

        system_prompt = build_ai_system_prompt(profile_text)

        openai_messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        for message in messages:
            role = message.get("role")
            content = message.get("content")

            if role not in ["user", "assistant"]:
                continue

            if not content:
                continue

            openai_messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        completion = client.chat.completions.create(
            model=deployment_name,
            messages=openai_messages,
            temperature=0.4,
        )

        ai_message = completion.choices[0].message.content

        if not ai_message:
            logger.warning("OpenAI returned an empty response.")
            return "Sorry, I could not generate a response."

        return ai_message

    except Exception:
        logger.exception("Failed to generate AI response.")
        return (
            "Sorry, something went wrong while generating a response. "
            "Please try again."
        )