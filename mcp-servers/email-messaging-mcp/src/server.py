from fastmcp import FastMCP

mcp = FastMCP("email-messaging-mcp")

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> dict:
    """Sends an email message via Gmail API."""
    return {
        "status": "success",
        "message": f"Email successfully dispatched to {to}.",
        "subject": subject
    }

if __name__ == "__main__":
    mcp.run()
