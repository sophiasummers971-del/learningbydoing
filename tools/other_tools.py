# coding=utf-8
import os
import subprocess

from core import HackingTool
from core import HackingToolsCollection
from tools.others.android_attack import AndroidAttackTools
from tools.others.email_verifier import EmailVerifyTools
from tools.others.hash_crack import HashCrackingTools
from tools.others.homograph_attacks import IDNHomographAttackTools
from tools.others.mix_tools import MixTools
from tools.others.payload_injection import PayloadInjectorTools
from tools.others.socialmedia import SocialMediaBruteforceTools
from tools.others.socialmedia_finder import SocialMediaFinderTools
from tools.others.web_crawling import WebCrawlingTools
from tools.others.wifi_jamming import WifiJammingTools

from rich.console import Console
from rich.theme import Theme
from rich.table import Table
from rich.panel import Panel

_theme = Theme({"purple": "#7B61FF"})
console = Console(theme=_theme)


class HatCloud(HackingTool):
    TITLE = "HatCloud(Bypass CloudFlare for IP)"
    DESCRIPTION = "HatCloud build in Ruby. It makes bypass in CloudFlare for " \
                  "discover real IP."
    INSTALL_COMMANDS = ["git clone https://github.com/HatBashBR/HatCloud.git"]
    PROJECT_URL = "https://github.com/HatBashBR/HatCloud"

    def run(self):
        site = input("Enter Site >> ")
        os.chdir("HatCloud")
        subprocess.run(["sudo", "ruby", "hatcloud.rb", "-b", site])


class OtherTools(HackingToolsCollection):
    TITLE = "Other tools"
    TOOLS = [
        SocialMediaBruteforceTools(),
        AndroidAttackTools(),
        HatCloud(),
        IDNHomographAttackTools(),
        EmailVerifyTools(),
        HashCrackingTools(),
        WifiJammingTools(),
        SocialMediaFinderTools(),
        PayloadInjectorTools(),
        WebCrawlingTools(),
        MixTools()
    ]

    def _get_attr(self, obj, *names, default=""):
        for n in names:
            if hasattr(obj, n):
                return getattr(obj, n)
        return default

    def pretty_print(self):
        table = Table(title="Other Tools", show_lines=True, expand=True)
        table.add_column("Title", style="purple", no_wrap=True)
        table.add_column("Description", style="purple")
        table.add_column("Project URL", style="purple", no_wrap=True)

        for t in self.TOOLS:
            title = self._get_attr(t, "TITLE", "Title", "title", default=t.__class__.__name__)
            desc = self._get_attr(t, "DESCRIPTION", "Description", "description", default="")
            url = self._get_attr(t, "PROJECT_URL", "PROJECT_URL", "PROJECT", "project_url", "projectUrl", default="")
            table.add_row(str(title), str(desc).strip().replace("\n", " "), str(url))

        panel = Panel(table, title="[purple]Available Tools[/purple]", border_style="purple")
        console.print(panel)


if __name__ == "__main__":
    tools = OtherTools()
    tools.pretty_print()
