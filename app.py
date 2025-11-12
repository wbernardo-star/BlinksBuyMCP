"""
Flask + MCP (OpenAI Model Context Protocol) — compliant skeleton
Requires: mcp==1.21.0, flask, flask-cors, gunicorn (for deploy)
"""

import os
import threading
from flask import Flask, jsonify, request, make_response
from mcp.server.fastmcp import FastMCP
from flask_cors import CORS

# ------------------ Flask (HTTP) ------------------
app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Add CORS headers to all responses (belt and suspenders approach)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
    return response

@app.route("/health", methods=["GET", "OPTIONS"])
def health():
    if request.method == "OPTIONS":
        # Handle preflight request
        return make_response('', 204)
    return jsonify({"ok": True, "message": "Flask + MCP server is healthy"})

# ------------------ MCP (STDIO) -------------------
mcp = FastMCP("flask-mcp-server")  # server name (shown to clients)

# Minimal example tools (safe & serializable). You can remove if you want no tools.
@mcp.tool()
def ping() -> dict:
    """Simple MCP health check."""
    return {"pong": True}

@mcp.tool()
def add_numbers(a: int, b: int) -> dict:
    """Add two integers."""
    return {"sum": a + b}

def run_mcp_stdio():
    # Runs the MCP server on STDIO (the transport most MCP hosts expect)
    # Do not block the Flask thread; run as daemon thread.
    mcp.run()

# ------------------ Entry point -------------------
if __name__ == "__main__":
    # Start MCP stdio server in background
    threading.Thread(target=run_mcp_stdio, daemon=True).start()

    # Start Flask HTTP server
    port = int(os.getenv("PORT", 3333))
    app.run(host="0.0.0.0", port=port)
