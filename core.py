import os
import shlex
import shutil
import subprocess
import sys
import webbrowser
from collections.abc import Callable
from platform import system

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import install

from constants import (
    THEME_PRIMARY, THEME_BORDER, THEME_ACCENT,
    THEME_SUCCESS, THEME_ERROR, THEME_WARNING,
    THEME_DIM, THEME_ARCHIVED, THEME_URL,
)

# Enable rich tracebacks globally
install()

_theme = Theme({
    "purple":   "#7B61FF",
    "success":  THEME_SUCCESS,
    "error":    THEME_ERROR,
    "warning":  THEME_WARNING,
    "archived": THEME_ARCHIVED,
    "url":      THEME_URL,
    "dim":      THEME_DIM,
})

# Single shared console — all tool files do: from core import console
console = Console(theme=_theme)


# ---------------------------------------------------------------------------
# Allowlist of base commands that tool definitions are permitted to execute.
# Any command whose first token (after an optional leading "sudo") is NOT in
# this set will be blocked before execution.
# ---------------------------------------------------------------------------
ALLOWED_BASE_COMMANDS: frozenset[str] = frozenset({
    # Package managers
    "apt", "apt-get", "yum", "dnf", "pacman", "brew",
    "pip", "pip3", "gem", "npm", "yarn", "go", "cargo",
    # Version control
    "git", "svn",
    # Build / compile
    "make", "cmake",
    # Language runtimes / interpreters
    "python", "python3", "ruby", "node", "java", "php", "perl",
    # Common shell utilities used by install scripts
    "sudo", "chmod", "chown", "mkdir", "cp", "mv", "rm",
    "tar", "unzip", "zip", "curl", "wget", "bash", "sh",
    # Screen / navigation used in chained commands
    "clear", "cls", "cd", "echo",
})


def _run_single_command(cmd: str, cwd: str | None = None) -> tuple[int, str | None]:
    """Execute one simple (non-chained) command with ``shell=False``.

    ``cd`` is emulated in-process by updating *cwd* so that subsequent
    sub-commands in a ``&&`` chain see the correct working directory.

    Returns ``(returncode, updated_cwd)``.
    """
    cmd = cmd.strip()
    if not cmd:
        return 0, cwd

    try:
        tokens = shlex.split(cmd)
    except ValueError:
        console.print(f"[error]Malformed command skipped: {cmd!r}[/error]")
        return 1, cwd

    if not tokens:
        return 0, cwd

    # Determine effective base command (skip a leading 'sudo')
    base = tokens[0] if tokens[0] != "sudo" else (tokens[1] if len(tokens) > 1 else "")
    base = os.path.basename(base)

    if base not in ALLOWED_BASE_COMMANDS:
        console.print(f"[error]Command blocked (not in allowlist): {base!r}[/error]")
        return 1, cwd

    # Emulate 'cd' in-process so subsequent sub-commands in a chain run in the
    # correct directory without requiring shell=True.
    if base == "cd":
        target = tokens[-1] if len(tokens) > 1 else os.environ.get("HOME", "")
        new_dir = target if os.path.isabs(target) else os.path.join(cwd or ".", target)
        return 0, os.path.normpath(new_dir)

    try:
        result = subprocess.run(tokens, shell=False, check=False, cwd=cwd)
        return result.returncode, cwd
    except (OSError, subprocess.SubprocessError) as exc:
        console.print(f"[error]Command execution failed: {exc}[/error]")
        return 1, cwd


def _execute_command(cmd: str) -> int:
    """Execute a tool command safely with allowlist validation.

    ``&&``-chained install/run commands are split and each sub-command is
    executed individually via :func:`_run_single_command` with
    ``shell=False``.  Working-directory context is preserved across ``cd``
    sub-commands.  Execution halts on the first non-zero return code.

    Returns the final process return-code (0 = success).
    """
    if not cmd or not cmd.strip():
        return 0

    cwd: str | None = None
    for sub_cmd in cmd.split("&&"):
        rc, cwd = _run_single_command(sub_cmd, cwd)
        if rc != 0:
            return rc
    return 0


def clear_screen():
    subprocess.run(["cls"] if system() == "Windows" else ["clear"], check=False)


def validate_input(ip, val_range: list) -> int | None:
    """Return the integer if it is in val_range, else None."""
    if not val_range:
        return None
    try:
        ip = int(ip)
        if ip in val_range:
            return ip
    except (TypeError, ValueError):
        pass
    return None


def _show_inline_help():
    """Quick help available from any menu level."""
    console.print(Panel(
        Text.assemble(
            ("  Navigation\n", "bold white"),
            ("  ─────────────────────────────────\n", "dim"),
            ("  1–N    ", "bold cyan"), ("select item\n", "white"),
            ("  97     ", "bold cyan"), ("install all (in category)\n", "white"),
            ("\n  Tool menu: Install, Run, Update, Open Folder\n", "dim"),
            ("  99     ", "bold cyan"), ("go back\n", "white"),
            ("  98     ", "bold cyan"), ("open project page / archived\n", "white"),
            ("  ?      ", "bold cyan"), ("show this help\n", "white"),
            ("  q      ", "bold cyan"), ("quit hackingtool\n", "white"),
        ),
        title="[bold magenta] ? Quick Help [/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    Prompt.ask("[dim]Press Enter to return[/dim]", default="")


class HackingTool:
    TITLE: str              = ""
    DESCRIPTION: str        = ""
    INSTALL_COMMANDS: list[str]  = []
    UNINSTALL_COMMANDS: list[str] = []
    RUN_COMMANDS: list[str]      = []
    OPTIONS: list[tuple[str, Callable]] = []
    PROJECT_URL: str        = ""

    # OS / capability metadata
    SUPPORTED_OS: list[str] = ["linux", "macos"]
    REQUIRES_ROOT: bool     = False
    REQUIRES_WIFI: bool     = False
    REQUIRES_GO: bool       = False
    REQUIRES_RUBY: bool     = False
    REQUIRES_JAVA: bool     = False
    REQUIRES_DOCKER: bool   = False

    # Tags for search/filter (e.g. ["osint", "web", "recon", "scanner"])
    TAGS: list[str]         = []

    # Archived tool flags
    ARCHIVED: bool          = False
    ARCHIVED_REASON: str    = ""

    def __init__(self, options=None, installable=True, runnable=True):
        options = options or []
        if not isinstance(options, list):
            raise TypeError("options must be a list of (option_name, option_fn) tuples")
        self.OPTIONS = []
        if installable:
            self.OPTIONS.append(("Install", self.install))
        if runnable:
            self.OPTIONS.append(("Run", self.run))
        self.OPTIONS.append(("Update", self.update))
        self.OPTIONS.append(("Open Folder", self.open_folder))
        self.OPTIONS.extend(options)

    @property
    def is_installed(self) -> bool:
        """Check if the tool's binary is on PATH or its clone dir exists."""
        if self.RUN_COMMANDS:
            cmd = self.RUN_COMMANDS[0]
            # Handle "cd foo && binary --help" pattern
            if "&&" in cmd:
                cmd = cmd.split("&&")[-1].strip()
            if cmd.startswith("sudo "):
                cmd = cmd[5:].strip()
            binary = cmd.split()[0] if cmd else ""
            if binary and binary not in (".", "echo", "cd"):
                if shutil.which(binary):
                    return True
        # Check if git clone target dir exists
        if self.INSTALL_COMMANDS:
            for ic in self.INSTALL_COMMANDS:
                if "git clone" in ic:
                    parts = ic.split()
                    repo_url = [p for p in parts if p.startswith("http")]
                    if repo_url:
                        dirname = repo_url[0].rstrip("/").rsplit("/", 1)[-1].replace(".git", "")
                        if os.path.isdir(dirname):
                            return True
        return False

    def show_info(self):
        desc = f"[cyan]{self.DESCRIPTION}[/cyan]"
        if self.PROJECT_URL:
            desc += f"\n[url]🔗 {self.PROJECT_URL}[/url]"
        if self.ARCHIVED:
            desc += f"\n[archived]⚠ ARCHIVED: {self.ARCHIVED_REASON}[/archived]"
        console.print(Panel(
            desc,
            title=f"[{THEME_PRIMARY}]{self.TITLE}[/{THEME_PRIMARY}]",
            border_style="purple",
            box=box.DOUBLE,
        ))

    def show_options(self, parent=None):
        """Iterative menu loop — no recursion, no stack growth."""
        while True:
            clear_screen()
            self.show_info()

            table = Table(title="Options", box=box.SIMPLE_HEAVY)
            table.add_column("No.", style="bold cyan", justify="center")
            table.add_column("Action", style="bold yellow")

            for index, option in enumerate(self.OPTIONS):
                table.add_row(str(index + 1), option[0])

            if self.PROJECT_URL:
                table.add_row("98", "Open Project Page")
            table.add_row("99", f"Back to {parent.TITLE if parent else 'Main Menu'}")
            console.print(table)
            console.print(
                "  [dim cyan]?[/dim cyan][dim]help  "
                "[/dim][dim cyan]q[/dim cyan][dim]uit  "
                "[/dim][dim cyan]99[/dim cyan][dim] back[/dim]"
            )

            raw = Prompt.ask("[bold cyan]╰─>[/bold cyan]", default="").strip().lower()
            if not raw:
                continue
            if raw in ("?", "help"):
                _show_inline_help()
                continue
            if raw in ("q", "quit", "exit"):
                raise SystemExit(0)

            try:
                choice = int(raw)
            except ValueError:
                console.print("[error]⚠ Enter a number, ? for help, or q to quit.[/error]")
                Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
                continue

            if choice == 99:
                return
            elif choice == 98 and self.PROJECT_URL:
                self.show_project_page()
            elif 1 <= choice <= len(self.OPTIONS):
                try:
                    self.OPTIONS[choice - 1][1]()
                except Exception:
                    console.print_exception(show_locals=True)
                Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            else:
                console.print("[error]⚠ Invalid option.[/error]")

    def before_install(self): pass

    def install(self):
        self.before_install()
        if isinstance(self.INSTALL_COMMANDS, (list, tuple)):
            for cmd in self.INSTALL_COMMANDS:
                console.print(f"[warning]→ {cmd}[/warning]")
                _execute_command(cmd)
        self.after_install()

    def after_install(self):
        console.print("[success]✔ Successfully installed![/success]")

    def before_uninstall(self) -> bool:
        return True

    def uninstall(self):
        if self.before_uninstall():
            if isinstance(self.UNINSTALL_COMMANDS, (list, tuple)):
                for cmd in self.UNINSTALL_COMMANDS:
                    console.print(f"[error]→ {cmd}[/error]")
                    _execute_command(cmd)
        self.after_uninstall()

    def after_uninstall(self): pass

    def update(self):
        """Smart update — detects install method and runs the right update command."""
        if not self.is_installed:
            console.print("[warning]Tool is not installed yet. Install it first.[/warning]")
            return

        updated = False
        for ic in (self.INSTALL_COMMANDS or []):
            if "git clone" in ic:
                # Extract repo dir name from clone command
                parts = ic.split()
                repo_urls = [p for p in parts if p.startswith("http")]
                if repo_urls:
                    dirname = repo_urls[0].rstrip("/").rsplit("/", 1)[-1].replace(".git", "")
                    if os.path.isdir(dirname):
                        console.print(f"[cyan]→ git -C {dirname} pull[/cyan]")
                        # Pass args as a list to avoid shell injection from dirname
                        subprocess.run(["git", "-C", dirname, "pull"], shell=False, check=False)
                        updated = True
            elif "pip install" in ic:
                # Re-run pip install (--upgrade)
                upgrade_cmd = ic.replace("pip install", "pip install --upgrade")
                console.print(f"[cyan]→ {upgrade_cmd}[/cyan]")
                _execute_command(upgrade_cmd)
                updated = True
            elif "go install" in ic:
                # Re-run go install (fetches latest)
                console.print(f"[cyan]→ {ic}[/cyan]")
                _execute_command(ic)
                updated = True
            elif "gem install" in ic:
                upgrade_cmd = ic.replace("gem install", "gem update")
                console.print(f"[cyan]→ {upgrade_cmd}[/cyan]")
                _execute_command(upgrade_cmd)
                updated = True

        if updated:
            console.print("[success]✔ Update complete![/success]")
        else:
            console.print("[dim]No automatic update method available for this tool.[/dim]")

    def _get_tool_dir(self) -> str | None:
        """Find the tool's local directory — clone target, pip location, or binary path."""
        # 1. Check git clone target dir
        for ic in (self.INSTALL_COMMANDS or []):
            if "git clone" in ic:
                parts = ic.split()
                # If last arg is not a URL, it's a custom dir name
                repo_urls = [p for p in parts if p.startswith("http")]
                if repo_urls:
                    dirname = repo_urls[0].rstrip("/").rsplit("/", 1)[-1].replace(".git", "")
                    # Check custom target dir (arg after URL)
                    url_idx = parts.index(repo_urls[0])
                    if url_idx + 1 < len(parts):
                        dirname = parts[url_idx + 1]
                    if os.path.isdir(dirname):
                        return os.path.abspath(dirname)

        # 2. Check binary location via which
        if self.RUN_COMMANDS:
            cmd = self.RUN_COMMANDS[0]
            if "&&" in cmd:
                # "cd foo && bar" → check "foo"
                cd_part = cmd.split("&&")[0].strip()
                if cd_part.startswith("cd "):
                    d = cd_part[3:].strip()
                    if os.path.isdir(d):
                        return os.path.abspath(d)
            binary = cmd.split()[0] if cmd else ""
            if binary.startswith("sudo"):
                binary = cmd.split()[1] if len(cmd.split()) > 1 else ""
            path = shutil.which(binary) if binary else None
            if path:
                return os.path.dirname(os.path.realpath(path))

        return None

    def open_folder(self):
        """Open the tool's directory in a new shell so the user can work manually."""
        tool_dir = self._get_tool_dir()
        if tool_dir:
            console.print(f"[success]Opening folder: {tool_dir}[/success]")
            console.print("[dim]Type 'exit' to return to hackingtool.[/dim]")
            # Use cwd= to set the working directory instead of building a shell
            # string with the path — prevents injection via specially crafted dir names.
            shell = os.environ.get("SHELL", "/bin/sh")
            subprocess.run([shell], cwd=tool_dir, shell=False, check=False)
        else:
            console.print("[warning]Tool directory not found.[/warning]")
            if self.PROJECT_URL:
                console.print(f"[dim]You can clone it manually:[/dim]")
                console.print(f"[cyan]  git clone {self.PROJECT_URL}.git[/cyan]")

    def before_run(self): pass

    def run(self):
        self.before_run()
        if isinstance(self.RUN_COMMANDS, (list, tuple)):
            for cmd in self.RUN_COMMANDS:
                console.print(f"[cyan]⚙ Running:[/cyan] [bold]{cmd}[/bold]")
                _execute_command(cmd)
        self.after_run()

    def after_run(self): pass

    def show_project_page(self):
        console.print(f"[url]🌐 Opening: {self.PROJECT_URL}[/url]")
        webbrowser.open_new_tab(self.PROJECT_URL)


class HackingToolsCollection:
    TITLE: str       = ""
    DESCRIPTION: str = ""
    TOOLS: list      = []

    def __init__(self):
        pass

    def show_info(self):
        console.rule(f"[{THEME_PRIMARY}]{self.TITLE}[/{THEME_PRIMARY}]", style="purple")
        if self.DESCRIPTION:
            console.print(f"[italic cyan]{self.DESCRIPTION}[/italic cyan]\n")

    def _active_tools(self) -> list:
        """Return tools that are not archived and are OS-compatible."""
        from os_detect import CURRENT_OS
        return [
            t for t in self.TOOLS
            if not getattr(t, "ARCHIVED", False)
            and CURRENT_OS.system in getattr(t, "SUPPORTED_OS", ["linux", "macos"])
        ]

    def _archived_tools(self) -> list:
        return [t for t in self.TOOLS if getattr(t, "ARCHIVED", False)]

    def _incompatible_tools(self) -> list:
        from os_detect import CURRENT_OS
        return [
            t for t in self.TOOLS
            if not getattr(t, "ARCHIVED", False)
            and CURRENT_OS.system not in getattr(t, "SUPPORTED_OS", ["linux", "macos"])
        ]

    def _show_archived_tools(self):
        """Show archived tools sub-menu (option 98)."""
        archived = self._archived_tools()
        if not archived:
            console.print("[dim]No archived tools in this category.[/dim]")
            Prompt.ask("[dim]Press Enter to return[/dim]", default="")
            return

        while True:
            clear_screen()
            console.rule(f"[archived]Archived Tools — {self.TITLE}[/archived]", style="yellow")

            table = Table(box=box.MINIMAL_DOUBLE_HEAD, show_lines=True)
            table.add_column("No.", justify="center", style="bold yellow")
            table.add_column("Tool", style="dim yellow")
            table.add_column("Reason", style="dim white")

            for i, tool in enumerate(archived):
                reason = getattr(tool, "ARCHIVED_REASON", "No reason given")
                table.add_row(str(i + 1), tool.TITLE, reason)

            table.add_row("99", "Back", "")
            console.print(table)

            raw = Prompt.ask("[bold yellow][?] Select[/bold yellow]", default="99")
            try:
                choice = int(raw)
            except ValueError:
                continue

            if choice == 99:
                return
            elif 1 <= choice <= len(archived):
                archived[choice - 1].show_options(parent=self)

    def show_options(self, parent=None):
        """Iterative menu loop — no recursion, no stack growth."""
        while True:
            clear_screen()
            self.show_info()

            active = self._active_tools()
            incompatible = self._incompatible_tools()
            archived = self._archived_tools()

            table = Table(title="Available Tools", box=box.SIMPLE_HEAD, show_lines=True)
            table.add_column("No.", justify="center", style="bold cyan", width=6)
            table.add_column("", width=2)  # installed indicator
            table.add_column("Tool", style="bold yellow", min_width=24)
            table.add_column("Description", style="white", overflow="fold")

            for index, tool in enumerate(active, start=1):
                desc = getattr(tool, "DESCRIPTION", "") or "—"
                desc = desc.splitlines()[0] if desc != "—" else "—"
                has_status = hasattr(tool, "is_installed")
                status = ("[green]✔[/green]" if tool.is_installed else "[dim]✘[/dim]") if has_status else ""
                table.add_row(str(index), status, tool.TITLE, desc)

            # Count not-installed tools for "Install All" label (skip sub-collections)
            not_installed = [t for t in active if hasattr(t, "is_installed") and not t.is_installed]
            if not_installed:
                table.add_row(
                    "[bold green]97[/bold green]", "",
                    f"[bold green]Install all ({len(not_installed)} not installed)[/bold green]", "",
                )
            if archived:
                table.add_row("[dim]98[/dim]", "", f"[archived]Archived tools ({len(archived)})[/archived]", "")
            if incompatible:
                console.print(f"[dim]({len(incompatible)} tools hidden — not supported on current OS)[/dim]")

            table.add_row("99", "", f"Back to {parent.TITLE if parent else 'Main Menu'}", "")
            console.print(table)
            console.print(
                "  [dim cyan]?[/dim cyan][dim]help  "
                "[/dim][dim cyan]q[/dim cyan][dim]uit  "
                "[/dim][dim cyan]99[/dim cyan][dim] back[/dim]"
            )

            raw = Prompt.ask("[bold cyan]╰─>[/bold cyan]", default="").strip().lower()
            if not raw:
                continue
            if raw in ("?", "help"):
                _show_inline_help()
                continue
            if raw in ("q", "quit", "exit"):
                raise SystemExit(0)

            try:
                choice = int(raw)
            except ValueError:
                console.print("[error]⚠ Enter a number, ? for help, or q to quit.[/error]")
                continue

            if choice == 99:
                return
            elif choice == 97 and not_installed:
                console.print(Panel(
                    f"[bold]Installing {len(not_installed)} tools...[/bold]",
                    border_style="green", box=box.ROUNDED,
                ))
                for i, tool in enumerate(not_installed, start=1):
                    console.print(f"\n[bold cyan]({i}/{len(not_installed)})[/bold cyan] {tool.TITLE}")
                    try:
                        tool.install()
                    except Exception:
                        console.print(f"[error]✘ Failed: {tool.TITLE}[/error]")
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            elif choice == 98 and archived:
                self._show_archived_tools()
            elif 1 <= choice <= len(active):
                try:
                    active[choice - 1].show_options(parent=self)
                except Exception:
                    console.print_exception(show_locals=True)
                    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            else:
                console.print("[error]⚠ Invalid option.[/error]")
