import json
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
You are Alex, a universal enterprise AI agent.
Analyze the user input and conversation history to classify the intent and extract all parameters into `tool_args`.

Supported Universal Intents & Tools:
1. `send_email`: Send email messages. Parameters: `recipient`, `subject`, `body`.
2. `create_calendar_event`: Schedule calendar meetings. Parameters: `title`, `recipient`, `date` (YYYY-MM-DD), `start_time` (HH:MM:SS), `end_time` (HH:MM:SS).
3. `list_calendar_events`: View calendar. Parameters: `date` or `date_range`.
4. `cancel_calendar_event`: Cancel meeting. Parameters: `event_title_or_id`.
5. `set_reminder`: Set reminders. Parameters: `reminder_text`, `time`.
6. `list_reminders`: Show reminders. Parameters: `status`.
7. `web_search`: Search web for live info. Parameters: `query`.
8. `resolve_person`: Look up contact details. Parameters: `name`.
9. `general_chat`: General QA or conversation. Parameters: `text`.

Always return valid structured output conforming to ExtractedIntent.
"""


def get_llm(temperature: float = 0.1):
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
    )


async def parse_intent_and_entities(input_text: str, memories: List[str], history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Universal LangChain Structured Output processing.
    """
    try:
        llm = get_llm(temperature=0.1)
        structured_llm = llm.with_structured_output(ExtractedIntent)

        messages = [
            SystemMessage(content=SYSTEM_INTENT_PROMPT),
            HumanMessage(content=f"User Prompt: {input_text}")
        ]

        result: ExtractedIntent = await structured_llm.ainvoke(messages)
        
        args = result.tool_args or {}
        args["input_text"] = input_text

        return {
            "intent": result.intent,
            "entities": args,
            "missing_slots": result.missing_slots
        }

    except Exception:
        # Robust universal fallback
        import re
        lower = input_text.lower()
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', input_text)
        recipient = emails[0] if emails else None

        intent = "general_chat"
        if any(w in lower for w in ["send a mail", "send mail", "send email", "email to", "mail to"]):
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
                "title": "Meeting",
                "subject": "Notification from Alex AI",
                "body": input_text,
                "query": input_text,
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
