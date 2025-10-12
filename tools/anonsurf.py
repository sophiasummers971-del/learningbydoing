# coding=utf-8
import os

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from core import HackingTool
from core import HackingToolsCollection

console = Console()
P_COLOR = "magenta"


class AnonymouslySurf(HackingTool):
    TITLE = "Anonymously Surf"
    DESCRIPTION = (
        "It automatically overwrites the RAM when\n"
        "the system is shutting down and also change Ip."
    )
    INSTALL_COMMANDS = [
        "sudo git clone https://github.com/Und3rf10w/kali-anonsurf.git",
        "cd kali-anonsurf && sudo ./installer.sh && cd .. && sudo rm -r kali-anonsurf",
    ]
    RUN_COMMANDS = ["sudo anonsurf start"]
    PROJECT_URL = "https://github.com/Und3rf10w/kali-anonsurf"

    def __init__(self):
        super(AnonymouslySurf, self).__init__([("Stop", self.stop)])

    def stop(self):
        console.print(Panel(Text(self.TITLE, justify="center"), style=f"bold {P_COLOR}"))
        console.print("Stopping Anonsurf...", style=f"bold {P_COLOR}")
        os.system("sudo anonsurf stop")


class Multitor(HackingTool):
    TITLE = "Multitor"
    DESCRIPTION = "How to stay in multi places at the same time"
    INSTALL_COMMANDS = [
        "sudo git clone https://github.com/trimstray/multitor.git",
        "cd multitor;sudo bash setup.sh install",
    ]
    RUN_COMMANDS = [
        "multitor --init 2 --user debian-tor --socks-port 9000 --control-port 9900 --proxy privoxy --haproxy"
    ]
    PROJECT_URL = "https://github.com/trimstray/multitor"

    def __init__(self):
        # keep original behavior (non-runnable) while still initializing
        super(Multitor, self).__init__(runnable=False)


class AnonSurfTools(HackingToolsCollection):
    TITLE = "Anonymously Hiding Tools"
    DESCRIPTION = ""
    TOOLS = [
        AnonymouslySurf(),
        Multitor(),
    ]
