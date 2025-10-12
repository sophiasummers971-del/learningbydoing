# coding=utf-8
from core import HackingTool
from core import HackingToolsCollection

from rich.console import Console
from rich.theme import Theme
from rich.table import Table
from rich.panel import Panel

_theme = Theme({"purple": "#7B61FF"})
console = Console(theme=_theme)


class Stitch(HackingTool):
    TITLE = "Stitch"
    DESCRIPTION = "Stitch is a cross platform python framework.\n" \
                  "which allows you to build custom payloads\n" \
                  "For Windows, Mac and Linux."
    INSTALL_COMMANDS = [
        "sudo git clone https://github.com/nathanlopez/Stitch.git",
        "cd Stitch;sudo pip install -r lnx_requirements.txt"
    ]
    RUN_COMMANDS = ["cd Stitch;python main.py"]
    PROJECT_URL = "https://github.com/nathanlopez/Stitch"


class Pyshell(HackingTool):
    TITLE = "Pyshell"
    DESCRIPTION = "Pyshell is a Rat Tool that can be able to download & upload " \
                  "files,\n Execute OS Command and more.."
    INSTALL_COMMANDS = [
        "sudo git clone https://github.com/knassar702/Pyshell.git;"
        "sudo pip install pyscreenshot python-nmap requests"
    ]
    RUN_COMMANDS = ["cd Pyshell;./Pyshell"]
    PROJECT_URL = "https://github.com/knassar702/pyshell"


class RemoteAdministrationTools(HackingToolsCollection):
    TITLE = "Remote Administrator Tools (RAT)"
    TOOLS = [
        Stitch(),
        Pyshell()
    ]

    def pretty_print(self):
        table = Table(title="Remote Administration Tools (RAT)", show_lines=True, expand=True)
        table.add_column("Title", style="purple", no_wrap=True)
        table.add_column("Description", style="purple")
        table.add_column("Project URL", style="purple", no_wrap=True)

        for t in self.TOOLS:
            desc = getattr(t, "DESCRIPTION", "") or ""
            url = getattr(t, "PROJECT_URL", "") or ""
            table.add_row(t.TITLE, desc.strip().replace("\n", " "), url)

        panel = Panel(table, title="[purple]Available Tools[/purple]", border_style="purple")
        console.print(panel)


if __name__ == "__main__":
    tools = RemoteAdministrationTools()
    tools.pretty_print()
