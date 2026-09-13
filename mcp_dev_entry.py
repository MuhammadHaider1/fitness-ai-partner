"""
Inspector launcher — sirf MCP Inspector (GUI debug) ke liye.

`mcp dev` ek plain .py file chahata hai (package module nahi). Ye file
project root se chalne par `app.mcp_server.server` ko import karti hai aur
FastMCP instance expose karti hai.

Run (project root se):
    venv/bin/mcp dev mcp_dev_entry.py:mcp
"""
from app.mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run()