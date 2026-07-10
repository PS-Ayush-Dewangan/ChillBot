"""
mcp_client.py — Reusable MCP client for ChillBot.

Manages connections to multiple MCP servers simultaneously,
discovers tools dynamically, and dispatches tool calls.

Uses the MCP Python SDK (mcp) with stdio transport to launch
each server as a subprocess.
"""

import asyncio
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from utils.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """
    Manages connections to one or more MCP servers.

    Usage:
        client = MCPClient()
        await client.connect("python", ["servers/info_server.py"], alias="info")
        tools = await client.discover_tools()
        result = await client.call_tool("get_weather", {"latitude": 51.5, "longitude": -0.1})
        await client.close()
    """

    def __init__(self) -> None:
        self._exit_stack = AsyncExitStack()
        # Maps tool_name -> ClientSession so we know which server owns each tool
        self._tool_registry: dict[str, ClientSession] = {}
        # All discovered Tool objects
        self._tools: list[Tool] = []
        # Named sessions for status reporting
        self._sessions: dict[str, ClientSession] = {}

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def connect(
        self,
        command: str,
        args: list[str],
        alias: str,
        env: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Launch an MCP server subprocess and establish a session.

        Args:
            command: Executable to run (e.g. "python").
            args:    Arguments to the executable (e.g. ["servers/info_server.py"]).
            alias:   Human-readable name for this server (used in logs/UI).
            env:     Optional extra environment variables for the subprocess.
        """
        params = StdioServerParameters(command=command, args=args, env=env)
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(params)
        )
        read_stream, write_stream = stdio_transport
        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        self._sessions[alias] = session
        logger.info("Connected to MCP server: %s", alias)

    async def discover_tools(self) -> list[Tool]:
        """
        Query every connected server for its tools and build the registry.

        Returns:
            Flat list of all Tool objects across all servers.
        """
        self._tools = []
        self._tool_registry = {}

        for alias, session in self._sessions.items():
            try:
                response = await session.list_tools()
                for tool in response.tools:
                    self._tools.append(tool)
                    self._tool_registry[tool.name] = session
                    logger.info("  Discovered tool: %s (from %s)", tool.name, alias)
            except Exception as exc:
                logger.error("Failed to discover tools from '%s': %s", alias, exc)

        return self._tools

    # ------------------------------------------------------------------
    # Tool invocation
    # ------------------------------------------------------------------

    async def call_tool(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """
        Call a named tool on the appropriate server.

        Args:
            tool_name:  Exact name of the tool to invoke.
            tool_input: Dictionary of arguments for the tool.

        Returns:
            The tool's result (typically a string or dict).

        Raises:
            ValueError: If the tool name is not in the registry.
        """
        session = self._tool_registry.get(tool_name)
        if session is None:
            raise ValueError(
                f"Unknown tool '{tool_name}'. "
                f"Available: {list(self._tool_registry.keys())}"
            )

        logger.info("Calling tool '%s' with input: %s", tool_name, tool_input)
        try:
            result = await session.call_tool(tool_name, tool_input)
            # MCP returns a CallToolResult; extract the text content
            if result.content:
                # Concatenate all text content blocks
                return "\n".join(
                    block.text for block in result.content if hasattr(block, "text")
                )
            return ""
        except Exception as exc:
            logger.error("Tool '%s' raised an error: %s", tool_name, exc)
            raise

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def get_tools(self) -> list[Tool]:
        """Return the cached list of discovered tools."""
        return self._tools

    def tools_description(self) -> str:
        """
        Build a human-readable (and LLM-readable) description of all tools.

        Returns:
            Multi-line string listing each tool, its description, and parameters.
        """
        if not self._tools:
            return "No tools available."

        lines: list[str] = []
        for tool in self._tools:
            # Build parameter summary
            params_schema = tool.inputSchema or {}
            properties = params_schema.get("properties", {})
            required = params_schema.get("required", [])
            param_parts = []
            for param_name, param_info in properties.items():
                req_marker = "*" if param_name in required else "?"
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                param_parts.append(f"  {req_marker} {param_name} ({param_type}): {param_desc}")

            params_str = "\n".join(param_parts) if param_parts else "  (no parameters)"
            lines.append(
                f"Tool: {tool.name}\n"
                f"Description: {tool.description or 'No description'}\n"
                f"Parameters:\n{params_str}"
            )

        return "\n\n".join(lines)

    def get_session_names(self) -> list[str]:
        """Return the aliases of all connected servers."""
        return list(self._sessions.keys())

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close all server connections and release resources."""
        await self._exit_stack.aclose()
        logger.info("All MCP server connections closed.")
