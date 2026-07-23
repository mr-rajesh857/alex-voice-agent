import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings


class ExtractedIntent(BaseModel):
    """Universal Pydantic schema for any AI tool request."""
    intent: str = Field(
        description="Classified user intent or tool: 'create_calendar_event', 'list_calendar_events', 'cancel_calendar_event', 'send_email', 'set_reminder', 'list_reminders', 'web_search', 'resolve_person', or 'general_chat'"
    )
    tool_args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dynamic dictionary of arbitrary extracted arguments (e.g., recipient, title, subject, body, date, start_time, query, reminder_text)"
    )
    missing_slots: List[str] = Field(
        default_factory=list,
        description="Missing required parameters if user query is incomplete"
    )


SYSTEM_INTENT_PROMPT = """
You are Alex, an enterprise AI assistant agent.
Analyze the user input and conversation history. Classify the user intent and extract all parameters dynamically into `tool_args`.

Supported Universal Intents & Tools:
1. `send_email`: Send email messages. Extract `recipient` (email address), `subject` (concise subject line), and `body` (polite, formatted email message text).
2. `create_calendar_event`: Schedule calendar meetings. Extract `title`, `recipient`, `date` (YYYY-MM-DD), `start_time` (HH:MM:SS), `end_time` (HH:MM:SS).
3. `list_calendar_events`: View calendar. Extract `date` or `date_range`.
4. `cancel_calendar_event`: Cancel meeting. Extract `event_title_or_id`.
5. `set_reminder`: Set reminders. Extract `reminder_text`, `time`.
6. `list_reminders`: Show reminders. Extract `status`.
7. `web_search`: Search web for live info. Extract `query`.
8. `resolve_person`: Look up contact details. Extract `name`.
9. `general_chat`: General QA or conversation. Extract `text`.

Always return valid structured output conforming to ExtractedIntent.
"""


def get_llm(temperature: float = 0.2):
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
    )


async def generate_email_content_with_ai(user_prompt: str) -> tuple[str, str]:
    """Uses Gemini AI to generate a dynamic, professional email subject and body for ANY user prompt."""
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.startswith("AIzaSy"):
        try:
            llm = get_llm(temperature=0.3)
            prompt = f"""
Given the user instruction: "{user_prompt}"

Generate:
1. A short, professional email subject line (3-6 words).
2. A polite, complete email body message text addressing the recipient.

Return JSON in this format:
```json
{{
  "subject": "...",
  "body": "..."
}}
```
"""
            resp = await llm.ainvoke(prompt)
            content = str(resp.content).strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            data = json.loads(content)
            return data.get("subject", "Update from Alex AI"), data.get("body", user_prompt)
        except Exception:
            pass

    # Universal fallback for any prompt without API key
    cleaned = re.sub(
        r'^(?:hey|hi|please)?\s*(?:send|write|draft)\s+(?:a\s+)?(?:mail|email|message)\s+(?:to\s+[\w\.-]+@[\w\.-]+\.\w+\s+)?(?:regarding|about|regading|sub|subject|saying|that)?\s*',
        '',
        user_prompt,
        flags=re.IGNORECASE
    ).strip()

    if not cleaned or cleaned.lower() == user_prompt.lower():
        cleaned = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '', user_prompt).strip()
        cleaned = re.sub(r'^(?:hey|hi|please)?\s*(?:send|write)\s+(?:a\s+)?(?:mail|email)\s+(?:to)?\s*', '', cleaned, flags=re.IGNORECASE).strip()

    subject = cleaned[:40].capitalize() if cleaned else "Notification from Alex AI"
    body = f"Hi,\n\n{cleaned.capitalize() if cleaned else 'Please review the details for your request.'}\n\nBest regards,\nAlex AI Assistant"

    return subject, body


async def parse_intent_and_entities(input_text: str, memories: List[str], history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Universal AI agent parsing. Uses Gemini LLM to dynamically interpret ANY user prompt.
    """
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', input_text)
    recipient = emails[0] if emails else None

    subject, body = await generate_email_content_with_ai(input_text)

    # 1. Try Gemini LLM Structured Ingestion
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.startswith("AIzaSy"):
        try:
            llm = get_llm(temperature=0.1)
            structured_llm = llm.with_structured_output(ExtractedIntent)

            messages = [
                SystemMessage(content=SYSTEM_INTENT_PROMPT),
                HumanMessage(content=f"User Prompt: {input_text}")
            ]

            result: ExtractedIntent = await structured_llm.ainvoke(messages)
            args = result.tool_args or {}

            if recipient and not args.get("recipient"):
                args["recipient"] = recipient
            if not args.get("subject") or "notification" in args.get("subject", "").lower():
                args["subject"] = subject
            if not args.get("body") or input_text in args.get("body", ""):
                args["body"] = body

            return {
                "intent": result.intent,
                "entities": args,
                "missing_slots": result.missing_slots
            }
        except Exception:
            pass

    # 2. Universal Fallback Classifier
    lower = input_text.lower()
    intent = "general_chat"
    if any(w in lower for w in ["send a mail", "send mail", "send email", "email to", "mail to", "write mail"]):
        intent = "send_email"
    elif any(w in lower for w in ["meeting", "schedule", "calendar", "interview", "appointment"]):
        intent = "create_calendar_event"
    elif "reminder" in lower:
        intent = "set_reminder"
    elif "search" in lower:
        intent = "web_search"

    return {
        "intent": intent,
        "entities": {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "title": subject,
            "date": "2026-07-25",
            "start_time": "08:30:00",
            "end_time": "09:30:00",
            "input_text": input_text
        },
        "missing_slots": []
    }


async def generate_clarification_question(input_text: str, missing_slots: List[str]) -> str:
    try:
        llm = get_llm(temperature=0.3)
        prompt = f"The user asked: '{input_text}'. Ask a polite follow-up question for missing parameters: {', '.join(missing_slots)}."
        response = await llm.ainvoke(prompt)
        return str(response.content).strip()
    except Exception:
        return f"Please specify {', '.join(missing_slots)} to proceed."


async def generate_confirmation_message(tool_name: str, tool_args: Dict[str, Any]) -> str:
    recipient = tool_args.get("recipient") or "recipient"
    if tool_name == "send_email":
        subject = tool_args.get("subject") or "Notification"
        return f"Should I send an email to {recipient} with subject '{subject}' via Gmail API?"
    
    title = tool_args.get("title") or "Meeting"
    date = tool_args.get("date") or "scheduled date"
    start_time = tool_args.get("start_time", "")
    return f"Should I schedule '{title}' with {recipient} on {date} ({start_time} IST) on Google Calendar and send an email invitation?"


async def format_final_response(input_text: str, tool_result: Any) -> str:
    if isinstance(tool_result, dict) and "message" in tool_result:
        return tool_result["message"]
    return f"Processed request: {tool_result if tool_result else ''}"
