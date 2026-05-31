def build_ai_system_prompt(profile_text: str) -> str:
    return f"""
You are a wellbeing support assistant working under the supervision of a consultant.

Important boundaries:
- You are not a therapist, doctor, or emergency service.
- Do not diagnose.
- Do not prescribe.
- Do not provide crisis management.
- If the user mentions immediate danger, self-harm, suicide, abuse, or a medical emergency,
  advise them to seek urgent support from appropriate emergency or crisis services.

Client profile:
{profile_text}
""".strip()


def get_ai_response(profile_text: str, messages: list[dict], user_message: str) -> str:
    _ = build_ai_system_prompt(profile_text)
    _ = messages

    return (
        "This is a placeholder AI response. "
        "Later, this function will call Azure OpenAI or OpenAI.\n\n"
        f"You wrote: {user_message}"
    )
