import os
import sys
import re
from config import Config
from parser import ResultParser
from modules.email_enum import EmailEnumerator
from modules.user_enum import UserEnumerator
from modules.dir_enum import DirEnumerator
from modules.endpoint_enum import EndpointEnumerator

BANNER = """
\033[1;32m
 ██╗    ██╗██╗     ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██║    ██║██║     ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██║ █╗ ██║██║     ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██║███╗██║██║     ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ╚███╔███╔╝███████╗██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
\033[0m\033[0;37m  Wordlist Recon Framework  |  made by \033[1;32m4nub1t\033[0m\033[0;37m  |  v1.1.0\033[0m
"""

_ANSI_RE = re.compile(r'\033\[[0-9;]*m')

def _strip_ansi(s: str) -> int:
    """Devuelve la longitud visible (sin códigos ANSI) de un string."""
    return len(_ANSI_RE.sub('', s))

def _build_menu() -> str:
    INNER_W = 41  # ancho interior visible entre | y |

    def row(content: str) -> str:
        visible_len = _strip_ansi(content)
        padding = INNER_W - visible_len - 1  # -1 por el espacio antes del |
        return f"  \033[1;37m|\033[0m {content}{' ' * padding}\033[1;37m|"

    border = "  \033[1;37m+" + "-" * INNER_W + "+\033[0m"

    lines = [
        border,
        row("\033[1;37m          SELECT MODULE"),
        border,
        row("  \033[1;32m[1]\033[1;37m  Email Enumeration"),
        row("  \033[1;32m[2]\033[1;37m  Username Enumeration"),
        row("  \033[1;32m[3]\033[1;37m  Directory Bruteforce"),
        row("  \033[1;32m[4]\033[1;37m  Endpoint Discovery"),
        row("  \033[1;31m[0]\033[1;37m  Exit"),
        border,
    ]
    return "\n" + "\n".join(lines) + "\n"

MENU = _build_menu()


def _normalize_headers(raw: str) -> str:
    """Acepta 'Key:Value,Key2:Value2' o formato dict Python "'Key': 'Value', ..." """
    if not raw:
        return ""
    if "': '" in raw or '": "' in raw:
        pairs = re.findall(r"""['"]([^'"]+)['"]\s*:\s*['"]([^'"]+)['"]""", raw)
        return ",".join(f"{k}:{v}" for k, v in pairs)
    return raw


def _normalize_params(raw: str) -> str:
    """Acepta 'key=value,key2=value2' o formato dict Python "'key': 'value', ..." """
    if not raw:
        return ""
    if "': '" in raw or '": "' in raw:
        pairs = re.findall(r"""['"]([^'"]+)['"]\s*:\s*['"]([^'"]+)['"]""", raw)
        return ",".join(f"{k}={v}" for k, v in pairs)
    return raw


class CLI:
    def __init__(self, config: Config):
        self.config = config
        self.parser = ResultParser()
        self.modules = {
            "1": EmailEnumerator,
            "2": UserEnumerator,
            "3": DirEnumerator,
            "4": EndpointEnumerator,
        }

    def _clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def _prompt_config(self, mode: str):
        print("\033[1;36m[*] Target Configuration\033[0m")
        target   = input("\033[0;37m    Target URL          : \033[0m").strip()
        wordlist = input("\033[0;37m    Wordlist path       : \033[0m").strip()
        threads  = input("\033[0;37m    Threads [50]        : \033[0m").strip() or "50"
        proxy    = input("\033[0;37m    Proxy [skip]        : \033[0m").strip()
        timeout  = input("\033[0;37m    Timeout secs [10]   : \033[0m").strip() or "10"

        self.config.set("target", target)
        self.config.set("wordlist", wordlist)
        self.config.set("threads", threads)
        self.config.set("proxy", proxy)
        self.config.set("timeout", timeout)

        print("\n\033[1;33m[*] Detection Options (leave blank to use baseline auto-detection)\033[0m")
        print("\033[0;37m    match-string  : mark as FOUND if response body contains this string\033[0m")
        print("\033[0;37m    invalid-string: mark as NOT FOUND if response body contains this string\033[0m")
        match   = input("\033[0;37m    match-string  [skip]: \033[0m").strip()
        invalid = input("\033[0;37m    invalid-string[skip]: \033[0m").strip()
        self.config.set("match_string", match)
        self.config.set("invalid_string", invalid)

        print("\n\033[1;33m[*] Advanced Options (leave blank to skip)\033[0m")
        headers = input("\033[0;37m    Extra headers  e.g. X-Requested-With:XMLHttpRequest,Referer:http://host/ : \033[0m").strip()
        params  = input("\033[0;37m    Extra POST params e.g. function=login : \033[0m").strip()
        self.config.set("extra_headers", _normalize_headers(headers))
        self.config.set("extra_params",  _normalize_params(params))

    def _run_module(self, key: str):
        mode_names = {"1": "email", "2": "user", "3": "dir", "4": "endpoint"}
        self._prompt_config(mode_names.get(key, ""))
        module_class = self.modules[key]
        module = module_class(self.config, self.parser)
        print(f"\n\033[1;36m[*] Starting module...\033[0m\n")
        module.run()
        input("\n\033[0;37m  Press Enter to return to menu...\033[0m")

    def run(self):
        self._clear()
        print(BANNER)
        while True:
            print(MENU)
            choice = input("\033[1;32mwlrecon\033[0m\033[0;37m > \033[0m").strip()
            if choice == "0":
                print("\n\033[0;37m[*] Exiting WLRecon. Stay sharp.\033[0m\n")
                sys.exit(0)
            elif choice in self.modules:
                self._clear()
                print(BANNER)
                self._run_module(choice)
                self._clear()
                print(BANNER)
            else:
                print("\033[1;31m[-] Invalid option.\033[0m")
