"""
MCP (Model Context Protocol) server for the Fitness AI Partner backend.

Is package ke andar `server.py` ek MCP server expose karta hai jo fitness
backend ki functionality ko MCP tools ke roop mein baahri clients (Claude
Desktop, Claude Code, waghaira) ke liye available karta hai.

Chalaane ke liye (project root se, venv activated):

    python -m app.mcp_server.server

Ya stdio/SSE stream bhi connect kiya ja sakta hai; dekho server.py > __main__.
"""