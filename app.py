#Blink_MCPMock_app.py

"""
Flask + OpenAI MCP (mcp==1.21.0) integrated with n8n (POST workflow)
--------------------------------------------------------------------
MCP tool: get_menu(category?) → POST to your n8n webhook
Works locally and on Railway
Fully MCP-compliant + CORS-enabled for Claude/Desktop testing
"""

import os
import sys
import threading
import logging
from typing import Optional

import requests
from flask import Flask, jsonify
from flask_cors import CORS
from mcp.server.fastmcp import FastMCP

# -------------------- Configuration --------------------
N8N_GET_MENU_URL = os.getenv("N8N_GET_MENU_URL", "").strip()
#AUTH_HEADER = os.getenv("N8N_AUTH_HEADER", "").strip()  # e.g., "Authorization"
#AUTH_TOKEN = os.getenv("N8N_AUTH_TOKEN", "").strip()    # e.g., "Bearer xyz"
#REQUEST_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "15"))  # seconds

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("mcp-app")

if not N8N_GET_MENU_URL:
    log.warning("N8N_GET_MENU_URL is not set — get_menu will fail until configured.")


# -------------------- Flask Setup --------------------
app = Flask(__name__)

# Allow Claude Desktop, browsers, or other local origins
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-API-Key"],
    expose_headers=["Content-Type"],
    methods=["GET", "POST", "OPTIONS"],
)

@app.get("/health")
def health():
    return jsonify({"ok": True, "message": "Flask + MCP is healthy"})


# -------------------- MCP Setup --------------------
mcp = FastMCP("flask-mcp-server")

def _build_headers():
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if AUTH_HEADER and AUTH_TOKEN:
        headers[AUTH_HEADER] = AUTH_TOKEN
    return headers


@mcp.tool()
def get_menu(category: Optional[str] = None) -> dict:
    """
    Fetch the current menu from an n8n workflow (POST request).
    Optionally include a category filter in the JSON body.
    """
    if not N8N_GET_MENU_URL:
        return {"ok": False, "error": "missing_config", "message": "N8N_GET_MENU_URL not set"}

    payload = {}
    if category:
        payload["category"] = category

    try:
        resp = requests.post(
            N8N_GET_MENU_URL,
            json=payload,
            headers=_build_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        # Normalize structure to {"items": [...]}
        if isinstance(data, dict):
            items = data.get("items", data.get("data", data))
            if not isinstance(items, list):
                items = [items]
        elif isinstance(data, list):
            items = data
        else:
            items = [data]

        return {"ok": True, "items": items}

    except requests.HTTPError as e:
        return {
            "ok": False,
            "error": "http_error",
            "status_code": e.response.status_code if e.response else None,
            "details": str(e),
            "body": (e.response.text[:300] if e.response and e.response.text else None),
        }
    except requests.RequestException as e:
        return {"ok": False, "error": "network_error", "details": str(e)}
    except ValueError as e:
        return {"ok": False, "error": "bad_json", "details": str(e)}


# -------------------- /tools (for browser testing) --------------------
@app.get("/tools")
def list_tools():
    try:
        tools = [
            {"name": "get_menu", "description": (get_menu.__doc__ or "").strip()},
        ]
        return jsonify({"tools": tools})
    except Exception as e:
        return jsonify({"error": "tool_enumeration_failed", "details": str(e)}), 500


# -------------------- Runner --------------------
def run_mcp():
    """Run the MCP server (STDIO transport)."""
    mcp.run()  # STDIO transport (for LLMs / Claude)

if __name__ == "__main__":
    threading.Thread(target=run_mcp, daemon=True).start()
    port = int(os.getenv("PORT", 3333))
    app.run(host="0.0.0.0", port=port)
