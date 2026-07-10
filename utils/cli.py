"""
cli.py — Rich terminal UI for ChillBot.

All rendering (banner, spinners, ReAct steps, final answer panels)
lives here so agent.py stays focused on logic.
"""

from contextlib import contextmanager
from typing import Generator

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.spinner import Spinner
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich import box

# Single shared console — import this everywhere instead of plain print()
console = Console(highlight=False)


# ---------------------------------------------------------------------------
# Colour / style constants
# ---------------------------------------------------------------------------

_STYLE_THOUGHT     = Style(color="cyan",    bold=False)
_STYLE_ACTION      = Style(color="yellow",  bold=True)
_STYLE_OBSERVATION = Style(color="green",   bold=False)
_STYLE_REFLECTION  = Style(color="magenta", bold=False)
_STYLE_ERROR       = Style(color="red",     bold=True)
_STYLE_DIM         = Style(color="grey50")


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def print_banner() -> None:
    """Print the ChillBot welcome banner."""
    banner = Text(justify="center")
    banner.append("\n🤖  ChillBot\n",        style=Style(color="bright_cyan", bold=True))
    banner.append("AI Personal Companion\n", style=Style(color="cyan"))
    banner.append("Powered by MCP + Ollama\n", style=Style(color="bright_black"))

    console.print(Panel(banner, box=box.DOUBLE, border_style="cyan", padding=(0, 4)))


# ---------------------------------------------------------------------------
# Server / tool discovery status
# ---------------------------------------------------------------------------

def print_server_status(session_names: list[str], tools: list) -> None:
    """
    Print a two-column table showing connected servers and discovered tools.

    Args:
        session_names: Aliases of connected MCP servers.
        tools:         List of discovered Tool objects.
    """
    # Server table
    server_labels = {
        "info": "Info Server   (Weather · Books · Movies)",
        "fun":  "Fun Server    (Jokes · Quotes)",
    }

    server_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    server_table.add_column(style="green bold")
    server_table.add_column(style="white")

    for alias in session_names:
        label = server_labels.get(alias, alias)
        server_table.add_row("✓", label)

    console.print(Panel(server_table, title="[bold cyan]Connected Servers[/]",
                        border_style="cyan", box=box.ROUNDED))

    # Tools table
    tool_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    tool_table.add_column(style="green bold")
    tool_table.add_column(style="bright_white bold")
    tool_table.add_column(style="grey50")

    for tool in tools:
        desc = (tool.description or "")[:60]
        tool_table.add_row("✓", tool.name, desc)

    console.print(Panel(tool_table, title="[bold cyan]Discovered Tools[/]",
                        border_style="cyan", box=box.ROUNDED))

    console.print()


# ---------------------------------------------------------------------------
# Spinner context manager
# ---------------------------------------------------------------------------

@contextmanager
def thinking_spinner(message: str = "Thinking...") -> Generator[Live, None, None]:
    """
    Display an animated spinner while the agent is working.

    Usage:
        with thinking_spinner("Calling tool..."):
            result = await some_async_call()
    """
    spinner = Spinner("dots", text=Text(f" {message}", style="cyan"))
    with Live(spinner, console=console, refresh_per_second=12, transient=True) as live:
        yield live


# ---------------------------------------------------------------------------
# ReAct step display
# ---------------------------------------------------------------------------

def print_thought(thought: str, iteration: int) -> None:
    """Print a reasoning thought with iteration label."""
    if not thought:
        return
    label = Text(f"  Step {iteration} · Thought  ", style=_STYLE_DIM)
    body  = Text(f"  {thought}", style=_STYLE_THOUGHT)
    console.print(label)
    console.print(body)


def print_action(action: str, action_input: dict) -> None:
    """Print a tool call action."""
    # Format the input params compactly
    params = ", ".join(f"{k}={repr(v)}" for k, v in action_input.items())
    line = Text()
    line.append("  🔧 Action  ", style=_STYLE_ACTION)
    line.append(f"{action}", style=Style(color="yellow", bold=True))
    if params:
        line.append(f"({params})", style=_STYLE_DIM)
    console.print(line)


def print_observation(observation: str) -> None:
    """Print a tool observation, truncated if very long."""
    preview = observation[:300] + ("…" if len(observation) > 300 else "")
    line = Text()
    line.append("  👁  Observation  ", style=_STYLE_OBSERVATION)
    line.append(preview, style=Style(color="bright_black"))
    console.print(line)
    console.print()


def print_reflection_status(is_correct: bool) -> None:
    """Print whether reflection approved or corrected the answer."""
    if is_correct:
        console.print(Text("  🔍 Reflection  ✓ Answer looks good", style=_STYLE_REFLECTION))
    else:
        console.print(Text("  🔍 Reflection  ✎ Answer was improved", style=_STYLE_REFLECTION))
    console.print()


# ---------------------------------------------------------------------------
# Final answer panel
# ---------------------------------------------------------------------------

def print_final_answer(answer: str) -> None:
    """
    Render the agent's final answer inside a styled panel.
    Treats the answer as Markdown so bold/emoji/lists render nicely.
    """
    console.print(
        Panel(
            Markdown(answer),
            title="[bold bright_cyan]🤖  ChillBot[/]",
            border_style="bright_cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


# ---------------------------------------------------------------------------
# Dividers & prompts
# ---------------------------------------------------------------------------

def print_divider() -> None:
    """Print a subtle horizontal rule between conversations."""
    console.print(Rule(style="grey30"))


def print_user_prompt() -> str:
    """
    Render the user input prompt and return the stripped input string.
    Returns empty string on EOF/interrupt (caller should handle exit).
    """
    try:
        console.print(Text("\n🧑  You", style=Style(color="bright_white", bold=True)),
                      end="")
        return console.input(Text("  › ", style="bright_white"))
    except (EOFError, KeyboardInterrupt):
        return ""


def print_error(message: str) -> None:
    """Print an error message in a red panel."""
    console.print(
        Panel(Text(message, style=_STYLE_ERROR),
              border_style="red", box=box.ROUNDED, padding=(0, 1))
    )


def print_goodbye() -> None:
    """Print a friendly exit message."""
    console.print(
        Panel(Text("Stay chill! See you next time 😎", justify="center",
                   style=Style(color="cyan", bold=True)),
              border_style="cyan", box=box.ROUNDED, padding=(0, 2))
    )


def print_help() -> None:
    """Print available slash-commands."""
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column(style="yellow bold")
    table.add_column(style="white")
    table.add_row("/tools",   "List all available MCP tools")
    table.add_row("/prefs",   "Show saved preferences")
    table.add_row("/clear",   "Clear the screen")
    table.add_row("/help",    "Show this help")
    table.add_row("quit/exit","Exit ChillBot")
    console.print(Panel(table, title="[bold cyan]Commands[/]",
                        border_style="cyan", box=box.ROUNDED))
