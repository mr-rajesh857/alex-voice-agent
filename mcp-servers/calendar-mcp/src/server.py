from fastmcp import FastMCP

mcp = FastMCP("calendar-mcp")

@mcp.tool()
def create_event(title: str, start: str, end: str = None, attendees: list = None) -> dict:
    """Creates a calendar event."""
    return {
        "status": "success",
        "event_id": "evt_101",
        "title": title,
        "start": start,
        "attendees": attendees or []
    }

@mcp.tool()
def list_events(date_range: str = "today") -> dict:
    """Lists calendar events for a given date range."""
    return {
        "status": "success",
        "events": [
            {"id": "evt_101", "title": "Team Sync", "start": "15:00"},
            {"id": "evt_102", "title": "Project Review", "start": "17:00"}
        ]
    }

if __name__ == "__main__":
    mcp.run()
