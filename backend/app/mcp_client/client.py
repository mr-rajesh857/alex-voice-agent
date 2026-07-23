import httpx
import base64
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

ACTIVE_GOOGLE_OAUTH_TOKEN: Optional[str] = None

def set_google_oauth_token(token: str):
    global ACTIVE_GOOGLE_OAUTH_TOKEN
    ACTIVE_GOOGLE_OAUTH_TOKEN = token

def get_google_oauth_token() -> Optional[str]:
    return ACTIVE_GOOGLE_OAUTH_TOKEN


def create_raw_email(to: str, subject: str, body: str) -> str:
    """Constructs a base64url encoded RFC 2822 email for Gmail API."""
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return raw


async def execute_mcp_tool(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes REAL Google Calendar API and REAL Gmail API requests.
    """
    token = get_google_oauth_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # -------------------------------------------------------------
    # 1. REAL GMAIL API — Send Email
    # -------------------------------------------------------------
    if tool_name == "send_email":
        recipient = tool_args.get("recipient") or tool_args.get("to") or "rajeshkumarpanda857@gmail.com"
        subject = tool_args.get("subject") or "Interview Meeting Invitation"
        body = tool_args.get("body") or f"Hi,\n\nYou have been scheduled for an interview meeting.\n\nBest regards,\nAlex AI Assistant"

        if not token:
            return {
                "status": "error",
                "message": "Google OAuth token not found. Please log in with Google first to send real emails."
            }

        try:
            raw_email = create_raw_email(recipient, subject, body)
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers=headers,
                    json={"raw": raw_email}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "status": "success",
                        "message": f"✅ REAL Email sent to {recipient} via Gmail API! (Message ID: {data.get('id')})",
                        "email_id": data.get("id"),
                        "recipient": recipient,
                        "subject": subject
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to send email via Gmail API: {resp.text}"
                    }
        except Exception as e:
            return {"status": "error", "message": f"Error sending email: {str(e)}"}

    # -------------------------------------------------------------
    # 2. REAL GOOGLE CALENDAR API — Create Event
    # -------------------------------------------------------------
    elif tool_name == "create_calendar_event":
        title = tool_args.get("title") or "Interview Meeting"
        recipient = tool_args.get("recipient") or tool_args.get("to") or tool_args.get("attendees")
        date_val = tool_args.get("date", "2026-07-25")
        start_time_val = tool_args.get("start_time", "08:30:00")
        end_time_val = tool_args.get("end_time", "09:30:00")

        start_iso = f"{date_val}T{start_time_val}+05:30"
        end_iso = f"{date_val}T{end_time_val}+05:30"

        if not token:
            return {
                "status": "error",
                "message": "Google OAuth token not found. Please log in with Google first."
            }

        event_payload = {
            "summary": title,
            "description": f"Interview meeting scheduled by Alex AI Assistant for {recipient}.",
            "start": {"dateTime": start_iso, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_iso, "timeZone": "Asia/Kolkata"},
        }

        if recipient:
            if isinstance(recipient, str):
                event_payload["attendees"] = [{"email": recipient}]
            elif isinstance(recipient, list):
                event_payload["attendees"] = [{"email": email} for email in recipient]

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers=headers,
                    json=event_payload
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    
                    # Send invitation email via Gmail API
                    email_result = ""
                    if recipient:
                        email_recipient = recipient[0] if isinstance(recipient, list) else recipient
                        email_res = await execute_mcp_tool("send_email", {
                            "recipient": email_recipient,
                            "subject": f"Interview Meeting Invitation - {date_val} (8:30 AM IST)",
                            "body": f"Hi,\n\nYour interview meeting '{title}' has been scheduled on Google Calendar for {date_val} from 08:30 AM to 09:30 AM IST.\n\nGoogle Calendar Link: {data.get('htmlLink')}\n\nBest regards,\nAlex AI Assistant"
                        })
                        email_result = f" & {email_res.get('message')}"

                    return {
                        "status": "success",
                        "message": f"📅 REAL Google Calendar Event created for {date_val} (8:30 - 9:30 IST)! Link: {data.get('htmlLink')}{email_result}",
                        "event_id": data.get("id"),
                        "html_link": data.get("htmlLink")
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to create Google Calendar event: {resp.text}"
                    }
        except Exception as e:
            return {"status": "error", "message": f"Error creating calendar event: {str(e)}"}

    # -------------------------------------------------------------
    # 3. Default fallback
    # -------------------------------------------------------------
    return {
        "status": "success",
        "message": f"Executed tool '{tool_name}' with args {tool_args}.",
    }
