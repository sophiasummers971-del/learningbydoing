from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.traceback import install
from rich.theme import Theme

import os
import sys
import webbrowser
from platform import system
from traceback import print_exc
from typing import Callable, List, Tuple

# Enable rich tracebacks
install()
_theme = Theme({"purple": "#7B61FF"})
console = Console(theme=_theme)


def clear_screen():
    os.system("cls" if system() == "Windows" else "clear")


def validate_input(ip, val_range):
    val_range = val_range or []
    try:
        ip = int(ip)
        if ip in val_range:
            return ip
    except Exception:
        return None
    return None


class HackingTool(object):
    TITLE: str = ""
    DESCRIPTION: str = ""
    INSTALL_COMMANDS: List[str] = []
    INSTALLATION_DIR: str = ""
    UNINSTALL_COMMANDS: List[str] = []
    RUN_COMMANDS: List[str] = []
    OPTIONS: List[Tuple[str, Callable]] = []
    PROJECT_URL: str = ""

    def __init__(self, options=None, installable=True, runnable=True):
        options = options or []
        if isinstance(options, list):
            self.OPTIONS = []
            if installable:
                self.OPTIONS.append(("Install", self.install))
            if runnable:
                self.OPTIONS.append(("Run", self.run))
            self.OPTIONS.extend(options)
        else:
            raise Exception("options must be a list of (option_name, option_fn) tuples")

    def show_info(self):
        desc = f"[cyan]{self.DESCRIPTION}[/cyan]"
        if self.PROJECT_URL:
            desc += f"\n[green]🔗 {self.PROJECT_URL}[/green]"
        console.print(Panel(desc, title=f"[bold purple]{self.TITLE}[/bold purple]", border_style="purple", box=box.DOUBLE))

    def show_options(self, parent=None):
        clear_screen()
        self.show_info()

        table = Table(title="Options", box=box.SIMPLE_HEAVY)
        table.add_column("No.", style="bold cyan", justify="center")
        table.add_column("Action", style="bold yellow")

        for index, option in enumerate(self.OPTIONS):
            table.add_row(str(index + 1), option[0])

        if self.PROJECT_URL:
            table.add_row("98", "Open Project Page")
        table.add_row("99", f"Back to {parent.TITLE if parent else 'Exit'}")

        console.print(table)

        option_index = input("\n[?] Select an option: ").strip()
        try:
            option_index = int(option_index)
            if option_index - 1 in range(len(self.OPTIONS)):
                ret_code = self.OPTIONS[option_index - 1][1]()
                if ret_code != 99:
                    input("\nPress [Enter] to continue...")
            elif option_index == 98:
                self.show_project_page()
            elif option_index == 99:
                if parent is None:
                    sys.exit()
                return 99
        except (TypeError, ValueError):
            console.print("[red]⚠ Please enter a valid option.[/red]")
            input("\nPress [Enter] to continue...")
        except Exception:
            console.print_exception(show_locals=True)
            input("\nPress [Enter] to continue...")
        return self.show_options(parent=parent)

    def before_install(self): pass

    def install(self):
        self.before_install()
        commands = list(self.INSTALL_COMMANDS) if isinstance(self.INSTALL_COMMANDS, (list, tuple)) else []

        if not commands:
            console.print("[yellow]No install commands defined for this tool.[/yellow]")
            return

        console.print(Panel(
            "[bold]Choose installation method[/bold]\n\n"
            "1) Install inside a new venv (recommended)\n"
            "2) Install with '--break' flag (sudo prefixed)\n"
            "3) Cancel",
            title="[purple]Install Method[/purple]", border_style="purple"
        ))
        choice = input("\n[?] Select method (1/2/3): ").strip()

        try:
            choice_i = int(choice)
        except Exception:
            console.print("[red]⚠ Invalid selection. Aborting install.[/red]")
            return

        if choice_i == 3:
            console.print("[yellow]Installation cancelled by user.[/yellow]")
            return

        use_venv = choice_i == 1
        use_break = choice_i == 2

        is_windows = system() == "Windows"

        def maybe_sudo(cmd: str) -> str:
            if is_windows:
                return cmd
            stripped = cmd.lstrip()
            if stripped.startswith("sudo "):
                return cmd
            return "sudo " + cmd

        import shlex
        import shutil

        def _handle_git_clone(orig_cmd: str, maybe_sudo_fn) -> bool:
            cmd = orig_cmd.strip()
            parts = shlex.split(cmd)
            if len(parts) < 3 or parts[0] != "git" or parts[1] != "clone":
                return None

            repo_url = parts[2]
            if len(parts) >= 4:
                target = parts[3]
            else:
                target = os.path.basename(repo_url.rstrip("/")).replace(".git", "")

            target_path = os.path.abspath(target)

            if not os.path.exists(target_path):
                run_cmd = maybe_sudo_fn(f'git clone {repo_url} "{target}"')
                console.print(f"[yellow]→ {run_cmd}[/yellow]")
                rc = os.system(run_cmd)
                return rc == 0

            is_git_repo = os.path.isdir(os.path.join(target_path, ".git"))

            try:
                is_empty = len(os.listdir(target_path)) == 0
            except Exception:
                is_empty = False

            if is_empty:
                run_cmd = maybe_sudo_fn(f'git clone {repo_url} "{target}"')
                console.print(f"[yellow]→ {run_cmd}[/yellow]")
                rc = os.system(run_cmd)
                return rc == 0

            console.print(Panel(
                f"[bold]Target '{target_path}' already exists and is not empty.[/bold]\n\n"
                "Choose action:\n"
                "1) Skip this git clone\n"
                "2) Remove existing directory and clone\n"
                "3) If repo, run 'git pull' inside existing directory\n"
                "4) Clone into a different directory",
                title="[purple]git clone conflict[/purple]",
                border_style="purple"
            ))

            choice = input("\n[?] Select (1/2/3/4): ").strip()
            try:
                choice_i = int(choice)
            except Exception:
                console.print("[red]Invalid selection — skipping by default.[/red]")
                return True

            if choice_i == 1:
                console.print("[yellow]Skipping git clone.[/yellow]")
                return True

            if choice_i == 2:
                rm_cmd = maybe_sudo_fn(f'rm -rf "{target_path}"')
                console.print(f"[yellow]→ {rm_cmd}[/yellow]")
                rc = os.system(rm_cmd)
                if rc != 0:
                    console.print(f"[red]Failed to remove {target_path} (exit {rc}).[/red]")
                    return False
                run_cmd = maybe_sudo_fn(f'git clone {repo_url} "{target}"')
                console.print(f"[yellow]→ {run_cmd}[/yellow]")
                rc2 = os.system(run_cmd)
                return rc2 == 0

            if choice_i == 3:
                if not is_git_repo:
                    console.print("[red]Existing dir is not a git repository — cannot pull.[/red]")
                    return False
                pull_cmd = maybe_sudo_fn(f'git -C "{target_path}" pull')
                console.print(f"[yellow]→ {pull_cmd}[/yellow]")
                rc = os.system(pull_cmd)
                return rc == 0

            if choice_i == 4:
                new_dir = input("Enter new directory name: ").strip()
                if not new_dir:
                    console.print("[red]No directory provided — skipping.[/red]")
                    return True
                run_cmd = maybe_sudo_fn(f'git clone {repo_url} "{new_dir}"')
                console.print(f"[yellow]→ {run_cmd}[/yellow]")
                rc = os.system(run_cmd)
                return rc == 0

            console.print("[yellow]No valid option selected — skipping git clone.[/yellow]")
            return True

        if use_venv:
            venv_dir = os.path.expanduser("~/.venv_tool")
            parent = os.path.dirname(venv_dir)
            if parent and not os.path.exists(parent):
                try:
                    os.makedirs(parent, exist_ok=True)
                except Exception:
                    console.print(f"[red]Unable to create parent directory for venv: {parent}[/red]")
                    return

            if is_windows:
                create_cmd = f'python -m venv "{venv_dir}"'
            else:
                create_cmd = f'python3 -m venv "{venv_dir}" || python -m venv "{venv_dir}"'

            console.print(f"[yellow]→ {maybe_sudo(create_cmd)}[/yellow]")
            rc = os.system(maybe_sudo(create_cmd))
            if rc != 0:
                console.print(f"[red]Failed to create venv (exit {rc}).[/red]")
                return

            if is_windows:
                venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
                venv_pip = os.path.join(venv_dir, "Scripts", "pip.exe")
            else:
                venv_python = os.path.join(venv_dir, "bin", "python")
                venv_pip = os.path.join(venv_dir, "bin", "pip")

            all_ok = True
            for orig_cmd in commands:
                cmd = orig_cmd.strip()
                lower = cmd.lower()

                if lower.startswith("pip ") or lower.startswith("pip3 ") or ("-m pip install" in lower):
                    parts = cmd.split()
                    if parts[0] in ("pip", "pip3"):
                        new_cmd = f'"{venv_pip}" ' + " ".join(parts[1:])
                    else:
                        rest = cmd[cmd.find("-m pip") + len("-m pip"):].strip()
                        new_cmd = f'"{venv_python}" -m pip {rest}'
                    cmd_to_run = maybe_sudo(new_cmd)
                elif lower.startswith("python ") or lower.startswith("python3 "):
                    parts = cmd.split()
                    parts[0] = f'"{venv_python}"'
                    cmd_to_run = maybe_sudo(" ".join(parts))
                elif cmd.strip().lower().startswith("git clone"):
                    ok = _handle_git_clone(cmd, maybe_sudo)
                    if ok is None:
                        cmd_to_run = maybe_sudo(cmd)
                        console.print(f"[yellow]→ {cmd_to_run}[/yellow]")
                        rc = os.system(cmd_to_run)
                        if rc != 0:
                            console.print(f"[red]Command failed with exit code {rc}: {cmd}[/red]")
                            all_ok = False
                            break
                        continue
                    else:
                        if not ok:
                            all_ok = False
                            break
                        else:
                            continue
                else:
                    cmd_to_run = maybe_sudo(cmd)

                console.print(f"[yellow]→ {cmd_to_run}[/yellow]")
                rc = os.system(cmd_to_run)
                if rc != 0:
                    console.print(f"[red]Command failed with exit code {rc}: {cmd}[/red]")
                    all_ok = False
                    break

            if all_ok:
                self.after_install()
            else:
                console.print("[red]✖ Installation encountered errors.[/red]")
            return

        if use_break:
            all_ok = True
            for orig_cmd in commands:
                cmd = orig_cmd
                lower_cmd = cmd.lower()

                skip_break = (
                    "git clone" in lower_cmd
                    or "wget" in lower_cmd
                    or "curl" in lower_cmd
                    or "http" in lower_cmd
                    or "https" in lower_cmd
                )

                if (not skip_break) and ("--break" not in cmd):
                    cmd = cmd.strip() + " --break"

                if cmd.strip().lower().startswith("git clone"):
                    ok = _handle_git_clone(cmd, maybe_sudo)
                    if ok is None:
                        cmd_to_run = maybe_sudo(cmd)
                        console.print(f"[yellow]→ {cmd_to_run}[/yellow]")
                        rc = os.system(cmd_to_run)
                        if rc != 0:
                            console.print(f"[red]Command failed with exit code {rc}: {cmd}[/red]")
                            all_ok = False
                            break
                        continue
                    else:
                        if not ok:
                            all_ok = False
                            break
                        else:
                            continue

                cmd_to_run = maybe_sudo(cmd)
                console.print(f"[yellow]→ {cmd_to_run}[/yellow]")
                rc = os.system(cmd_to_run)
                if rc != 0:
                    console.print(f"[red]Command failed with exit code {rc}: {cmd}[/red]")
                    all_ok = False
                    break

            if all_ok:
                self.after_install()
            else:
                console.print("[red]✖ Installation encountered errors.[/red]")


    def after_install(self):
        console.print("[green]✔ Successfully installed![/green]")

    def before_uninstall(self) -> bool:
        return True

    def uninstall(self):
        if self.before_uninstall():
            if isinstance(self.UNINSTALL_COMMANDS, (list, tuple)):
                for UNINSTALL_COMMAND in self.UNINSTALL_COMMANDS:
                    console.print(f"[red]→ {UNINSTALL_COMMAND}[/red]")
                    os.system(UNINSTALL_COMMAND)
            self.after_uninstall()

    def after_uninstall(self): pass

    def before_run(self): pass

    def run(self):
        self.before_run()
        if isinstance(self.RUN_COMMANDS, (list, tuple)):
            for RUN_COMMAND in self.RUN_COMMANDS:
                console.print(f"[cyan]⚙ Running:[/cyan] [bold]{RUN_COMMAND}[/bold]")
                os.system(RUN_COMMAND)
            self.after_run()

    def after_run(self): pass

    def is_installed(self, dir_to_check=None):
        console.print("[yellow]⚠ Unimplemented: DO NOT USE[/yellow]")
        return "?"

    def show_project_page(self):
        console.print(f"[blue]🌐 Opening project page: {self.PROJECT_URL}[/blue]")
        webbrowser.open_new_tab(self.PROJECT_URL)


class HackingToolsCollection(object):
    TITLE: str = ""
    DESCRIPTION: str = ""
    TOOLS: List = []

    def __init__(self):
        pass

    def show_info(self):
        console.rule(f"[bold purple]{self.TITLE}[/bold purple]", style="purple")
        console.print(f"[italic cyan]{self.DESCRIPTION}[/italic cyan]\n")

    def show_options(self, parent=None):
        clear_screen()
        self.show_info()

        table = Table(title="Available Tools", box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column("No.", justify="center", style="bold cyan")
        table.add_column("Tool Name", style="bold yellow")

        for index, tool in enumerate(self.TOOLS):
            table.add_row(str(index), tool.TITLE)

        table.add_row("99", f"Back to {parent.TITLE if parent else 'Exit'}")
        console.print(table)

        tool_index = input("\n[?] Choose a tool: ").strip()
        try:
            tool_index = int(tool_index)
            if tool_index in range(len(self.TOOLS)):
                ret_code = self.TOOLS[tool_index].show_options(parent=self)
                if ret_code != 99:
                    input("\nPress [Enter] to continue...")
            elif tool_index == 99:
                if parent is None:
                    sys.exit()
                return 99
        except (TypeError, ValueError):
            console.print("[red]⚠ Please enter a valid option.[/red]")
            input("\nPress [Enter] to continue...")
        except Exception:
            console.print_exception(show_locals=True)
            input("\nPress [Enter] to continue...")
        return self.show_options(parent=parent)
