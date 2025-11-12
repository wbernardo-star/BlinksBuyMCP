import os
from flask import Flask, request, jsonify, abort
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()  # loads .env for local dev

MCP_SHARED_SECRET = os.getenv("MCP_SHARED_SECRET", "")
app = Flask(__name__)

# ----- Schemas -----
class GetMenuInput(BaseModel): pass

class GetMenuOutput(BaseModel):
    items: list

class CreateOrderInput(BaseModel):
    item: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    address: str = Field(..., min_length=3)

class CreateOrderOutput(BaseModel):
    order_id: str
    status: str

class GetOrderStatusInput(BaseModel):
    order_id: str = Field(..., min_length=1)

class GetOrderStatusOutput(BaseModel):
    order_id: str
    status: str
    eta: Optional[str] = None

# ----- Tool handlers -----
from api_client import get_menu as api_get_menu, create_order as api_create_order, get_order_status as api_get_order_status

def tool_get_menu(_: Dict[str, Any]) -> Dict[str, Any]:
    data = api_get_menu()
    return GetMenuOutput(items=data.get("items", data)).model_dump()

def tool_create_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    args = CreateOrderInput(**payload)
    data = api_create_order(args.item, args.quantity, args.address)
    return CreateOrderOutput(order_id=data["order_id"], status=data["status"]).model_dump()

def tool_get_order_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    args = GetOrderStatusInput(**payload)
    data = api_get_order_status(args.order_id)
    return GetOrderStatusOutput(
        order_id=data["order_id"],
        status=data["status"],
        eta=data.get("eta")
    ).model_dump()

TOOLS = {
    "get_menu": {
        "description": "Fetch the current menu items from the food API",
        "input_schema": GetMenuInput.model_json_schema(),
        "output_schema": GetMenuOutput.model_json_schema(),
        "handler": tool_get_menu,
    },
    "create_order": {
        "description": "Create a new order",
        "input_schema": CreateOrderInput.model_json_schema(),
        "output_schema": CreateOrderOutput.model_json_schema(),
        "handler": tool_create_order,
    },
    "get_order_status": {
        "description": "Check order status by order_id",
        "input_schema": GetOrderStatusInput.model_json_schema(),
        "output_schema": GetOrderStatusOutput.model_json_schema(),
        "handler": tool_get_order_status,
    },
}

def require_secret():
    if MCP_SHARED_SECRET:
        if request.headers.get("X-MCP-Secret") != MCP_SHARED_SECRET:
            abort(401, description="Invalid or missing X-MCP-Secret")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/mcp/discover")
def discover():
    require_secret()
    tools = [
        {
            "name": name,
            "description": meta["description"],
            "input_schema": meta["input_schema"],
            "output_schema": meta["output_schema"],
        }
        for name, meta in TOOLS.items()
    ]
    return jsonify({"server": {"name": "mcp-food", "version": "0.1.0"}, "tools": tools})

@app.post("/mcp/call")
def call_tool():
    require_secret()
    try:
        body = request.get_json(force=True) or {}
        tool = body.get("tool")
        tool_input = body.get("input", {})
        if tool not in TOOLS:
            abort(404, description=f"Unknown tool '{tool}'")
        result = TOOLS[tool]["handler"](tool_input)
        return jsonify({"ok": True, "tool": tool, "result": result})
    except ValidationError as ve:
        return jsonify({"ok": False, "error": "validation_error", "details": ve.errors()}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": "server_error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3333")))
