import json
import sys

STATUS_COLORS = {
    200: "\033[1;32m",
    201: "\033[1;32m",
    204: "\033[1;32m",
    301: "\033[1;33m",
    302: "\033[1;33m",
    401: "\033[1;35m",
    403: "\033[1;35m",
    404: "\033[0;37m",
    500: "\033[1;31m",
}

RESET  = "\033[0m"
GREEN  = "\033[1;32m"
RED    = "\033[1;31m"
CYAN   = "\033[1;36m"
GRAY   = "\033[0;37m"
YELLOW = "\033[1;33m"
BOLD   = "\033[1m"

class ResultParser:
    def __init__(self):
        self._hits: list[dict] = []

    def parse_line(self, line: str) -> dict | None:
        line = line.strip()
        if not line:
            return None
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None

    def format_result(self, data: dict) -> str | None:
        rtype  = data.get("type", "")
        result = data.get("result", "")
        status = data.get("status", 0)
        length = data.get("length", 0)
        found  = data.get("found", False)
        error  = data.get("error", "")

        if error:
            return f"{RED}[!] ERROR: {error}{RESET}"

        color = STATUS_COLORS.get(status, GRAY)

        if rtype == "progress":
            total   = data.get("total", 0)
            current = data.get("current", 0)
            pct     = (current / total * 100) if total > 0 else 0
            sys.stdout.write(f"\r{CYAN}[~] Progress: {current}/{total} ({pct:.1f}%){RESET}   ")
            sys.stdout.flush()
            return None

        if rtype == "summary":
            return None

        if not found:
            return None

        length_str = f" [{length}b]" if length else ""

        if rtype == "dir":
            return f"{GREEN}[+] FOUND:       {result}{RESET}{GRAY}  {color}{status}{RESET}{GRAY}{length_str}{RESET}"
        if rtype == "endpoint":
            return f"{GREEN}[+] ENDPOINT:    {result}{RESET}{GRAY}  {color}{status}{RESET}{GRAY}{length_str}{RESET}"
        if rtype == "user":
            return f"{GREEN}[+] VALID USER:  {result}{RESET}{GRAY}  {color}{status}{RESET}{GRAY}{length_str}{RESET}"
        if rtype == "email":
            return f"{GREEN}[+] VALID EMAIL: {result}{RESET}{GRAY}  {color}{status}{RESET}{GRAY}{length_str}{RESET}"

        return None

    def print_result(self, data: dict):
        rtype = data.get("type", "")
        found = data.get("found", False)

        if rtype == "progress":
            self.format_result(data)
            return

        if rtype == "summary":
            self._print_summary(data)
            return

        if found:
            self._hits.append(data)
            sys.stdout.write("\r" + " " * 70 + "\r")
            sys.stdout.flush()
            line = self.format_result(data)
            if line:
                print(line)

    def _print_summary(self, data: dict):
        total      = data.get("total", 0)
        found_count = data.get("found_count", 0)
        elapsed    = data.get("elapsed_ms", 0)

        print()
        print(f"\n{CYAN}{'─' * 55}{RESET}")
        print(f"{BOLD}  SCAN RESULTS SUMMARY{RESET}")
        print(f"{CYAN}{'─' * 55}{RESET}")

        if not self._hits:
            print(f"{GRAY}  No results found.{RESET}")
        else:
            type_groups: dict[str, list[dict]] = {}
            for hit in self._hits:
                t = hit.get("type", "unknown")
                type_groups.setdefault(t, []).append(hit)

            labels = {
                "dir":      "DIRECTORIES / PATHS",
                "endpoint": "ENDPOINTS",
                "user":     "VALID USERS",
                "email":    "VALID EMAILS",
            }

            for rtype, hits in type_groups.items():
                label = labels.get(rtype, rtype.upper())
                print(f"\n{YELLOW}  {label} ({len(hits)}){RESET}")
                print(f"{GRAY}  {'─' * 45}{RESET}")
                for hit in hits:
                    result = hit.get("result", "")
                    status = hit.get("status", 0)
                    length = hit.get("length", 0)
                    color  = STATUS_COLORS.get(status, GRAY)
                    print(f"  {GREEN}>{RESET} {result:<35} {color}{status}{RESET}  {GRAY}[{length}b]{RESET}")

        print(f"\n{CYAN}{'─' * 55}{RESET}")
        print(f"  {GRAY}Tested:{RESET} {total}   {GRAY}Found:{RESET} {GREEN}{found_count}{RESET}   {GRAY}Time:{RESET} {elapsed}ms")
        print(f"{CYAN}{'─' * 55}{RESET}\n")
