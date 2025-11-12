#Blink_MCPMock_app.py
"""
Flask + OpenAI Model Context Protocol (MCP) Server
--------------------------------------------------
Flask for HTTP routes (health, tools)
CORS for Claude Desktop & browser access
FastMCP for MCP (stdio protocol)
Compatible with mcp==1.21.0
Safe /tools endpoint that won't 500
"""

import os
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from mcp.server.fastmcp import FastMCP

# -------------------- Flask Setup --------------------
app = Flask(__name__)
CORS(app)  # allow requests from Claude Desktop or browsers

@app.get("/health")
def health():
    """Simple health endpoint to confirm the server is alive."""
    return jsonify({"ok": True, "message": "Flask + MCP is healthy"})

# -------------------- MCP Setup --------------------
mcp = FastMCP("flask-mcp-server")  # MCP server name shown to clients

# Example MCP tool 1
@mcp.tool()
def ping() -> dict:
    """Simple MCP health-check tool."""
    return {"pong": True}

# Example MCP tool 2
@mcp.tool()
def add_numbers(a: int, b: int) -> dict:
    """Add two integers together."""
    return {"sum": a + b}

# -------------------- Fixed /tools route --------------------
@app.get("/tools")
def list_tools():
    """
    List the registered MCP tools for browser inspection.
    Handles both public and internal registries safely.
    """
    tools = []

    # Try common internal registries (for future/backward compatibility)
    registry = (
        getattr(mcp, "tools", None)
        or getattr(mcp, "_tools", None)
        or getattr(getattr(mcp, "server", None), "tools", None)
    )

    try:
        if isinstance(registry, dict) and registry:
            for t in registry.values():
                name = getattr(t, "name", None) or getattr(t, "id", None) or "unknown"
                desc = (
                    getattr(t, "description", None)
                    or getattr(getattr(t, "func", None), "__doc__", None)
                    or ""
                )
                tools.append({"name": name, "description": (desc or "").strip()})
        else:
            # Fallback: manually list known functions
            tools = [
                {"name": "ping", "description": (ping.__doc__ or "").strip()},
                {"name": "add_numbers", "description": (add_numbers.__doc__ or "").strip()},
            ]
        return jsonify({"tools": tools})
    except Exception as e:
        # Return structured error instead of a 500
        return jsonify({"error": "tool_enumeration_failed", "details": str(e)}), 500

# -------------------- MCP Runner --------------------
def run_mcp():
    """Run the MCP server (STDIO transport)."""
    mcp.run()  # stdio transport by default

# -------------------- Main Entry --------------------
if __name__ == "__main__":
    # Start MCP stdio server in background
    threading.Thread(target=run_mcp, daemon=True).start()

    # Start Flask HTTP server
    port = int(os.getenv("PORT", 3333))
    app.run(host="0.0.0.0", port=port)
