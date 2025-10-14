#!/usr/bin/env python3
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
import os
import sys
import subprocess

console = Console()

ASCII = r"""
███████╗██╗  ██╗███╗   ██╗███████╗██╗   ██╗    
╚══███╔╝██║  ██║████╗  ██║╚══███╔╝██║   ██║    
  ███╔╝ ███████║██╔██╗ ██║  ███╔╝ ██║   ██║    
 ███╔╝  ╚════██║██║╚██╗██║ ███╔╝  ██║   ██║    
███████╗     ██║██║ ╚████║███████╗╚██████╔╝    
╚══════╝     ╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝     
                                              
"""

purple = "bold #7B61FF"
green = "bold green"
red = "bold red"
yellow = "bold yellow"
blue = "bold blue"

console.print(Panel(Text(ASCII, justify="center"), style=purple, padding=(1,2)))

if os.geteuid() != 0:
    console.print(f"[{red}][ERROR][/{red}] This script must be run as root.")
    sys.exit(1)

install_dir = "/usr/share/hackingtool"

try:
    os.chdir(install_dir)
except Exception:
    console.print(f"[{red}][ERROR][/{red}] Could not change to directory containing install.sh.")
    sys.exit(1)

console.print(f"[{yellow}][*][/{yellow}] Checking Internet Connection ..\n")
ok = False
urls = ["https://www.google.com", "https://www.github.com"]
for u in urls:
    try:
        r = subprocess.run(["curl", "-s", "-m", "10", u], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            ok = True
            break
    except FileNotFoundError:
        pass

if ok:
    console.print(f"[{green}][✔] Internet connection is OK [✔][/{green}]\n")
else:
    console.print(f"[{red}][✘] Please check your internet connection[✘][/{red}]\n")
    sys.exit(1)

console.print("[*]Marking hackingtool directory as safe-directory")
cfg = subprocess.run(["git", "config", "--global", "--add", "safe.directory", install_dir])
if cfg.returncode != 0:
    console.print(f"[{red}][ERROR][/{red}] Failed to mark safe.directory.")
    sys.exit(1)

console.print(f"[{blue}][INFO][/{blue}] Updating repository and tool...")
pull = subprocess.run(["git", "pull"])
if pull.returncode != 0:
    console.print(f"[{red}][ERROR][/{red}] Failed to update repository or tool.")
    sys.exit(1)

console.print(f"[{green}][INFO][/{green}] Running installation script...")
run_inst = subprocess.run(["bash", "install.sh"])
if run_inst.returncode != 0:
    console.print(f"[{red}][ERROR][/{red}] Failed to run installation script.")
    sys.exit(1)

console.print(f"[{green}][SUCCESS][/{green}] Tool updated successfully.")

menu_table = Table(show_header=False, box=None)
menu_table.add_row(Text("Index 99 → Exit", style=purple))
console.print(Panel(menu_table, title="Return to Menu", style=purple))

try:
    Prompt.ask("Press Enter to finish", default="")
except KeyboardInterrupt:
    pass

sys.exit(0)
