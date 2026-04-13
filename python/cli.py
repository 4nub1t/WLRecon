import os
import sys
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

MENU = """
\033[1;37m  +---------------------------------------+
  |           SELECT MODULE               |
  +---------------------------------------+
  |  \033[1;32m[1]\033[1;37m  Email Enumeration               |
  |  \033[1;32m[2]\033[1;37m  Username Enumeration            |
  |  \033[1;32m[3]\033[1;37m  Directory Bruteforce            |
  |  \033[1;32m[4]\033[1;37m  Endpoint Discovery              |
  |  \033[1;31m[0]\033[1;37m  Exit                            |
  +---------------------------------------+
\033[0m"""

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

        # Advanced detection options — shown for all modules
        print("\n\033[1;33m[*] Detection Options (leave blank to use baseline auto-detection)\033[0m")
        print("\033[0;37m    match-string  : mark as FOUND if response body contains this string\033[0m")
        print("\033[0;37m    invalid-string: mark as NOT FOUND if response body contains this string\033[0m")
        match   = input("\033[0;37m    match-string  [skip]: \033[0m").strip()
        invalid = input("\033[0;37m    invalid-string[skip]: \033[0m").strip()
        self.config.set("match_string", match)
        self.config.set("invalid_string", invalid)

        # Extra headers and params for advanced targets
        print("\n\033[1;33m[*] Advanced Options (leave blank to skip)\033[0m")
        headers = input("\033[0;37m    Extra headers  e.g. X-Requested-With:XMLHttpRequest,Referer:http://host/ : \033[0m").strip()
        params  = input("\033[0;37m    Extra POST params e.g. function=login : \033[0m").strip()
        self.config.set("extra_headers", headers)
        self.config.set("extra_params", params)

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
