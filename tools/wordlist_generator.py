# coding=utf-8
import os
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from core import HackingTool
from core import HackingToolsCollection

console = Console()


class Cupp(HackingTool):
    TITLE = "Cupp"
    DESCRIPTION = "WlCreator is a C program that can create all possibilities of passwords,\n " \
                  "and you can choose Length, Lowercase, Capital, Numbers and Special Chars"
    INSTALL_COMMANDS = ["git clone https://github.com/Mebus/cupp.git"]
    RUN_COMMANDS = ["cd cupp && python3 cupp.py -i"]
    PROJECT_URL = "https://github.com/Mebus/cupp"

    def show_info(self):
        panel = Panel(
            f"[bold magenta]{self.TITLE}[/bold magenta]\n\n"
            f"[cyan]{self.DESCRIPTION}[/cyan]\n\n"
            f"[green]Repository:[/green] [underline blue]{self.PROJECT_URL}[/underline blue]",
            border_style="magenta",
            box=box.ROUNDED,
        )
        console.print(panel)


class WlCreator(HackingTool):
    TITLE = "WordlistCreator"
    DESCRIPTION = "WlCreator is a C program that can create all possibilities" \
                  " of passwords,\n and you can choose Length, Lowercase, " \
                  "Capital, Numbers and Special Chars"
    INSTALL_COMMANDS = ["sudo git clone https://github.com/Z4nzu/wlcreator.git"]
    RUN_COMMANDS = [
        "cd wlcreator && sudo gcc -o wlcreator wlcreator.c && ./wlcreator 5"]
    PROJECT_URL = "https://github.com/Z4nzu/wlcreator"

    def show_info(self):
        panel = Panel(
            f"[bold magenta]{self.TITLE}[/bold magenta]\n\n"
            f"[cyan]{self.DESCRIPTION}[/cyan]\n\n"
            f"[green]Repository:[/green] [underline blue]{self.PROJECT_URL}[/underline blue]",
            border_style="magenta",
            box=box.ROUNDED,
        )
        console.print(panel)


class GoblinWordGenerator(HackingTool):
    TITLE = "Goblin WordGenerator"
    DESCRIPTION = "Goblin WordGenerator"
    INSTALL_COMMANDS = [
        "sudo git clone https://github.com/UndeadSec/GoblinWordGenerator.git"]
    RUN_COMMANDS = ["cd GoblinWordGenerator && python3 goblin.py"]
    PROJECT_URL = "https://github.com/UndeadSec/GoblinWordGenerator.git"

    def show_info(self):
        panel = Panel(
            f"[bold magenta]{self.TITLE}[/bold magenta]\n\n"
            f"[cyan]{self.DESCRIPTION}[/cyan]\n\n"
            f"[green]Repository:[/green] [underline blue]{self.PROJECT_URL}[/underline blue]",
            border_style="magenta",
            box=box.ROUNDED,
        )
        console.print(panel)


class showme(HackingTool):
    TITLE = "Password list (1.4 Billion Clear Text Password)"
    DESCRIPTION = "This tool allows you to perform OSINT and reconnaissance on " \
                  "an organisation or an individual. It allows one to search " \
                  "1.4 Billion clear text credentials which was dumped as " \
                  "part of BreachCompilation leak. This database makes " \
                  "finding passwords faster and easier than ever before."
    INSTALL_COMMANDS = [
        "sudo git clone https://github.com/Viralmaniar/SMWYG-Show-Me-What-You-Got.git",
        "cd SMWYG-Show-Me-What-You-Got && pip3 install -r requirements.txt"
    ]
    RUN_COMMANDS = ["cd SMWYG-Show-Me-What-You-Got && python SMWYG.py"]
    PROJECT_URL = "https://github.com/Viralmaniar/SMWYG-Show-Me-What-You-Got"

    def show_info(self):
        panel = Panel(
            f"[bold magenta]{self.TITLE}[/bold magenta]\n\n"
            f"[cyan]{self.DESCRIPTION}[/cyan]\n\n"
            f"[green]Repository:[/green] [underline blue]{self.PROJECT_URL}[/underline blue]",
            border_style="magenta",
            box=box.ROUNDED,
        )
        console.print(panel)


class WordlistGeneratorTools(HackingToolsCollection):
    TITLE = "Wordlist Generator"
    TOOLS = [
        Cupp(),
        WlCreator(),
        GoblinWordGenerator(),
        showme()
    ]

    def show_info(self):
        header = Panel(f"[bold white on magenta] {self.TITLE} [/bold white on magenta]",
                       border_style="magenta", box=box.DOUBLE)
        console.print(header)
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
        table.add_column("#", justify="center", style="cyan", width=4)
        table.add_column("Tool", style="bold")
        table.add_column("Description", style="dim", overflow="fold")

        for idx, t in enumerate(self.TOOLS, start=1):
            desc = getattr(t, "DESCRIPTION", "") or ""
            table.add_row(str(idx), t.TITLE, desc)

        console.print(table)
