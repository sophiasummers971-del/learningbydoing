# coding=utf-8
import os
import sys
from time import sleep

from core import HackingTool
from core import HackingToolsCollection

from rich.console import Console
from rich.theme import Theme
from rich.table import Table
from rich.panel import Panel

_theme = Theme({"purple": "#7B61FF"})
console = Console(theme=_theme)


class UpdateTool(HackingTool):
    TITLE = "Update Tool or System"
    DESCRIPTION = "Update Tool or System"

    def __init__(self):
        super(UpdateTool, self).__init__([
            ("Update System", self.update_sys),
            ("Update Hackingtool", self.update_ht)
        ], installable=False, runnable=False)

    def update_sys(self):
        os.system("sudo apt update && sudo apt full-upgrade -y")
        os.system(
            "sudo apt-get install tor openssl curl && sudo apt-get update tor openssl curl")
        os.system("sudo apt-get install python3-pip")

    def update_ht(self):
        os.system("sudo chmod +x /etc/;"
                  "sudo chmod +x /usr/share/doc;"
                  "sudo rm -rf /usr/share/doc/hackingtool/;"
                  "cd /etc/;"
                  "sudo rm -rf /etc/hackingtool/;"
                  "mkdir hackingtool;"
                  "cd hackingtool;"
                  "git clone https://github.com/Z4nzu/hackingtool.git;"
                  "cd hackingtool;"
                  "sudo chmod +x install.sh;"
                  "./install.sh")


class UninstallTool(HackingTool):
    TITLE = "Uninstall HackingTool"
    DESCRIPTION = "Uninstall HackingTool"

    def __init__(self):
        super(UninstallTool, self).__init__([
            ('Uninstall', self.uninstall)
        ], installable=False, runnable=False)

    def uninstall(self):
        print("hackingtool started to uninstall..\n")
        sleep(1)
        os.system("sudo chmod +x /etc/;"
                  "sudo chmod +x /usr/share/doc;"
                  "sudo rm -rf /usr/share/doc/hackingtool/;"
                  "cd /etc/;"
                  "sudo rm -rf /etc/hackingtool/;")
        print("\nHackingtool Successfully Uninstalled... Goodbye.")
        sys.exit()


class ToolManager(HackingToolsCollection):
    TITLE = "Update or Uninstall | Hackingtool"
    TOOLS = [
        UpdateTool(),
        UninstallTool()
    ]

    def pretty_print(self):
        table = Table(title="Tool Manager — Update / Uninstall", show_lines=True, expand=True)
        table.add_column("Title", style="purple", no_wrap=True)
        table.add_column("Description", style="purple")

        for t in self.TOOLS:
            desc = getattr(t, "DESCRIPTION", "") or ""
            table.add_row(t.TITLE, desc.strip().replace("\n", " "))

        panel = Panel(table, title="[purple]Available Manager Tools[/purple]", border_style="purple")
        console.print(panel)


if __name__ == "__main__":
    manager = ToolManager()
    manager.pretty_print()
