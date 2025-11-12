"""
Full Flask + MCP Server using OpenAI Model Context Protocol (MCP)
----------------------------------------------------------------
This script:
- Runs a Flask app (for health and HTTP endpoints)
- Starts an MCP server (protocol-compliant, using FastMCP)
"""

import os
import threading
from flask import Flask, jsonify
from mcp.server.fastmcp import FastMCP

# ------------------------------------------------------------
# Flask Setup
# ------------------------------------------------------------
app = Flask(__name__)

@app.route("/health")
def health():
    """Simple health check for HTTP"""
    return jsonify({"ok": True, "message": "Flask + MCP server is healthy"})


# ------------------------------------------------------------
# MCP Setup
# ------------------------------------------------------------
mcp = FastMCP("flask-mcp-server")

# Example MCP tool — feel free to replace or add more later
@mcp.tool()
def ping() -> dict:
    """A simple health-check tool exposed via MCP."""
    return {"pong": True, "source": "MCP running inside Flask"}


@mcp.tool()
def add_numbers(a: int, b: int) -> dict:
    """Example arithmetic tool to show argument passing."""
    return {"sum": a + b}


# ------------------------------------------------------------
# Threaded MCP Runner
# ------------------------------------------------------------
def run_mcp_server():
    """
    Runs the MCP server via stdio (protocol-compliant).
    This allows AI assistants or local LLM clients to connect via MCP.
    """
    print("Starting MCP server (stdio transport)...")
    mcp.run_stdio()


# ------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    # Run MCP in background thread (stdio-based)
    threading.Thread(target=run_mcp_server, daemon=True).start()

    # Run Flask normally for HTTP
    port = int(os.getenv("PORT", 3333))
    print(f"Running Flask on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
