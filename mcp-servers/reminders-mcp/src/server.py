from fastmcp import FastMCP

mcp = FastMCP("reminders-mcp")

@mcp.tool()
def set_reminder(text: str, time: str) -> dict:
    """Sets a new reminder."""
    return {
        "status": "success",
        "reminder_id": "rem_202",
        "text": text,
        "time": time
    }

if __name__ == "__main__":
    mcp.run()
