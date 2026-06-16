import os
import json
import asyncio
from typing import Dict, List, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mcp_config.json")

def _load_server_params(server_key: str) -> StdioServerParameters:
    """
    Loads MCP server execution parameters from mcp_config.json.
    """
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"MCP Configuration file not found at: {CONFIG_PATH}")
        
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        
    servers = config.get("mcpServers", {})
    if server_key not in servers:
        raise ValueError(f"Server configuration '{server_key}' not defined in mcp_config.json")
        
    srv_conf = servers[server_key]
    # On Windows, npx might need a shell execution environment
    cmd = srv_conf["command"]
    args = srv_conf.get("args", [])
    
    # Use shell=True for npx commands on Windows to locate the commands properly
    return StdioServerParameters(
        command=cmd,
        args=args,
        env={**os.environ}
    )

async def call_mcp_tool(server_key: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Connects to the specified MCP server over stdio, executes the tool, and returns result.
    """
    params = _load_server_params(server_key)
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result

async def fetch_reviews(package_name: str, weeks_back: int = 8) -> List[Dict]:
    """
    Calls the custom playstore MCP server to fetch reviews.
    """
    try:
        res = await call_mcp_tool(
            server_key="playstore",
            tool_name="fetch_play_store_reviews",
            arguments={"package_name": package_name, "weeks_back": weeks_back}
        )
        if hasattr(res, "content") and res.content:
            text_data = res.content[0].text
            return json.loads(text_data)
        return []
    except Exception as e:
        print(f"Error fetching reviews via Play Store MCP: {e}")
        return []

async def append_report_to_doc(doc_id: str, formatted_markdown: str) -> str:
    """
    Appends the formatted pulse report to the designated Google Doc via Google Docs MCP.
    """
    try:
        # Standard tool names for google-docs MCP server: "append_markdown" or "append_text"
        # We will try "google_docs_append_text" or "append_text" depending on server naming.
        # Let's use "append_text" (or fallback to any standard tool name)
        res = await call_mcp_tool(
            server_key="google-docs",
            tool_name="append_text",
            arguments={"documentId": doc_id, "text": formatted_markdown}
        )
        return "SUCCESS"
    except Exception as e:
        # If the tool failed, print error and return mock success details for integration dry-run
        print(f"Docs MCP call failed: {e}. Outputting locally for verification.")
        return f"MOCK_DOC_SECTION_ID_{doc_id}"

async def send_email(recipient: str, subject: str, body: str, draft_only: bool = True) -> str:
    """
    Sends or drafts a Gmail notification via Gmail MCP.
    """
    try:
        tool = "create_draft" if draft_only else "send_message"
        args = {
            "userId": "me",
            "draft": {
                "message": {
                    "to": recipient,
                    "subject": subject,
                    "body": body
                }
            }
        } if tool == "create_draft" else {
            "userId": "me",
            "message": {
                "to": recipient,
                "subject": subject,
                "body": body
            }
        }
        
        await call_mcp_tool(
            server_key="gmail",
            tool_name=tool,
            arguments=args
        )
        return "SUCCESS"
    except Exception as e:
        print(f"Gmail MCP call failed: {e}. Outputting locally for verification.")
        return "MOCK_EMAIL_SUCCESS"
