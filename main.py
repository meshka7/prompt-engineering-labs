import os
import re
import json
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

# ===================== INIT =====================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Create a .env file with OPENAI_API_KEY=... or export it in your shell."
    )

client = OpenAI(api_key=OPENAI_API_KEY)

# You can bump to "gpt-4.1" if you want.
MODEL = "gpt-4o-mini"


def llm(messages: List[Dict[str, str]], temperature: float = 0) -> str:
    """Call the LLM chat completion and return string content."""
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
        )
        return (r.choices[0].message.content or "").strip()
    except Exception as e:
        # Fail closed with a readable message; do not crash the flow.
        return f"(LLM error: {e})"


SYSTEM_PROMPT = """You are RegBot, a concise, friendly English-speaking registration assistant for a brokerage.
- Guide the user through KYC/registration step-by-step.
- Be short, clear, neutral. Ask for missing/invalid fields if needed.
- If user types 'help', explain ONLY the CURRENT field in simple words.
- NEVER invent values. NEVER submit without explicit user confirmation.
- When all required fields are collected, produce a short human summary (not JSON).
Language: English.
"""

# ===================== REGISTRATION SCHEMA =====================
# Add/modify fields here; the bot adapts automatically.
SCHEMA: List[Dict[str, Any]] = [
    {
        "key": "first_name",
        "question": "Please enter your First Name (as in your ID):",
        "required": True,
        "help": "Type your legal first name exactly as it appears in your ID.",
        "validate": r"^[A-Za-z\-]{1,}$",
    },
    {
        "key": "last_name",
        "question": "Please enter your Last Name (as in your ID):",
        "required": True,
        "help": "Type your legal last name exactly as it appears in your ID. Hyphen is allowed.",
        "validate": r"^[A-Za-z\-]{2,}$",
    },
    {
        "key": "country",
        "question": "Country of tax residency:",
        "required": True,
        "help": "Where you are legally required to pay taxes.",
        "validate": r"^[A-Za-z\s\-]{2,}$",
    },
    {
        "key": "passport_number",
        "question": "Passport number (no spaces):",
        "required": True,
        "help": "Found on the photo page. Letters and digits only.",
        "validate": r"^[A-Za-z0-9]{6,20}$",
    },
    {
        "key": "source_of_funds",
        "question": "Source of funds (salary/business/investments/etc.):",
        "required": True,
        "help": "Briefly and truthfully describe where your funds come from.",
        "validate": r"^.{3,}$",
    },
    {
        "key": "investment_experience_years",
        "question": "Investment experience in years (integer, 0 if none):",
        "required": False,
        "help": "If you have no experience, enter 0.",
        "validate": r"^\d{1,2}$",
    },
]


# ===================== HELPERS =====================
def is_valid(value: str, pattern: Optional[str]) -> bool:
    if not pattern:
        return True
    return re.match(pattern, value) is not None


def explain_field(field: Dict[str, Any], user_utterance: Optional[str] = None) -> str:
    """Ask LLM to explain the current field briefly."""
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Explain to the user the CURRENT form field and how to fill it correctly. "
                "Be brief and practical.\n"
                f"Field question: {field['question']}\n"
                f"Hint: {field.get('help','')}\n"
                f"Regex format: {field.get('validate','')}\n"
                f"User question: {user_utterance or ''}"
            ),
        },
    ]
    return llm(msgs)


def summarize_answers(answers: Dict[str, Any]) -> str:
    """Ask LLM for a human summary of collected answers for confirmation."""
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Create a short, clear human summary of the registration answers for final user confirmation. "
                "Do not add any new data; rephrase only.\n"
                f"Data: {json.dumps(answers, ensure_ascii=False)}"
            ),
        },
    ]
    return llm(msgs)


# ===================== MAIN LOOP =====================
def run_registration() -> None:
    print(
        "👋 Hello! I am RegBot. Let's go through a short registration.\n"
        "Tips: type 'help' for an explanation of the CURRENT field, or 'quit' to exit.\n"
    )

    answers: Dict[str, Any] = {}
    dialog_ctx: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    for field in SCHEMA:
        key = field["key"]

        while True:
            user_input = input(f"{field['question']} ").strip()

            if user_input.lower() == "quit":
                print("Exit. Your data is not saved.")
                return

            if user_input.lower() == "help":
                print(explain_field(field))
                continue

            # Required → not empty
            if field["required"] and not user_input:
                print("❌ This field is required. Enter a value or type 'help'.")
                continue

            # Regex validation
            if user_input and not is_valid(user_input, field.get("validate")):
                print("❌ Invalid format. Try again or type 'help'.")
                continue

            answers[key] = user_input
            dialog_ctx.append(
                {"role": "user", "content": f"{field['question']} -> {user_input}"}
            )
            break

    # Summary + confirmation
    print("\n🧾 Summary of your answers:")
    print(summarize_answers(answers))

    confirm = input("\nConfirm and produce JSON for backend (yes/no)? ").strip().lower()
    if confirm == "yes":
        print("\n✅ Final JSON:")
        print(json.dumps(answers, ensure_ascii=False, indent=2))
    else:
        print("OK, cancelled. Nothing saved.")


if __name__ == "__main__":
    run_registration()
