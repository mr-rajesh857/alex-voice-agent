from fastmcp import FastMCP

mcp = FastMCP("search-rag-mcp")

@mcp.tool()
def web_search(query: str) -> dict:
    """Performs web search for real-time information."""
    return {
        "status": "success",
        "results": [
            {"title": f"Latest info on {query}", "snippet": f"Summary details regarding {query}."}
        ]
    }

if __name__ == "__main__":
    mcp.run()
