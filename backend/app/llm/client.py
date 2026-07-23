import json
import re
from typing import Dict, Any, List
from datetime import datetime, timezone
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.llm.prompts import (
    INTENT_EXTRACTION_PROMPT,
    CLARIFICATION_PROMPT,
    CONFIRMATION_PROMPT,
    RESPONSE_FORMATTER_PROMPT
)

def get_llm(temperature: float = 0.2):
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
    )

def extract_email_and_params(input_text: str) -> Dict[str, Any]:
    """Helper to extract recipient emails, meeting titles, dates, and times from text."""
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', input_text)
    recipient = emails[0] if emails else None
    
    title = "Interview Meeting"
    if "interview" in input_text.lower():
        title = "Interview Meeting"
    elif "sync" in input_text.lower():
        title = "Team Sync Meeting"

    # Extract date if present (e.g. 25.07.2026 or 2026-07-25)
    date_match = re.search(r'(\d{1,2})[\.\/-](\d{1,2})[\.\/-](\d{4})', input_text)
    date_str = None
    if date_match:
        day, month, year = date_match.groups()
        date_str = f"{year}-{int(month):02d}-{int(day):02d}"

    # Extract time (e.g. 8.30 to 9.30)
    time_match = re.search(r'(\d{1,2})[\.\:](\d{2})\s*(?:to|-)\s*(\d{1,2})[\.\:](\d{2})', input_text)
    start_time_str = "08:30:00"
    end_time_str = "09:30:00"
    if time_match:
        sh, sm, eh, em = time_match.groups()
        start_time_str = f"{int(sh):02d}:{int(sm):02d}:00"
        end_time_str = f"{int(eh):02d}:{int(em):02d}:00"

    return {
        "recipient": recipient,
        "title": title,
        "date": date_str or "2026-07-25",
        "start_time": start_time_str,
        "end_time": end_time_str
    }

async def parse_intent_and_entities(input_text: str, memories: List[str], history: List[Dict[str, str]]) -> Dict[str, Any]:
    extracted = extract_email_and_params(input_text)
    lower = input_text.lower()

    if any(w in lower for w in ["meeting", "schedule", "calendar", "mail", "interview"]):
        return {
            "intent": "create_calendar_event",
            "entities": extracted,
            "missing_slots": []
        }
    elif "reminder" in lower:
        return {
            "intent": "set_reminder",
            "entities": {"reminder_text": input_text, "time": "Today at 6:00 PM"},
            "missing_slots": []
        }
    elif "search" in lower:
        return {
            "intent": "web_search",
            "entities": {"query": input_text},
            "missing_slots": []
        }
    return {
        "intent": "general_chat",
        "entities": {"text": input_text},
        "missing_slots": []
    }

async def generate_clarification_question(input_text: str, missing_slots: List[str]) -> str:
    slot_name = missing_slots[0] if missing_slots else "details"
    return f"Kis {slot_name} pe schedule karu?"

async def generate_confirmation_message(tool_name: str, tool_args: Dict[str, Any]) -> str:
    recipient = tool_args.get("recipient") or "recipient"
    title = tool_args.get("title") or "Meeting"
    date = tool_args.get("date") or "25.07.2026"
    return f"Should I schedule '{title}' with {recipient} on {date} (8:30 - 9:30 IST) on Google Calendar and send an invitation email via Gmail?"

async def format_final_response(input_text: str, tool_result: Any) -> str:
    if isinstance(tool_result, dict) and "message" in tool_result:
        return tool_result["message"]
    return f"Done! {tool_result if tool_result else ''}"
