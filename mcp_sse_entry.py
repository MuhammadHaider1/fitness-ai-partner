"""
SSE server launcher — GUI (MCP Inspector) testing ke liye.

MCP server ko SSE transport par expose karta hai (127.0.0.1:9000), taake MCP
Inspector browser UI us URL se connect kare. Port 8000 se bachta hai (wo
FastAPI API ka port hai).

Run (project root se):
    venv/bin/python mcp_sse_entry.py
"""
import uvicorn

from app.mcp_server.server import mcp

if __name__ == "__main__":
    app = mcp.sse_app()
    uvicorn.run(app, host="127.0.0.1", port=9000, log_level="info")