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

RESET = "\033[0m"
GREEN = "\033[1;32m"
RED   = "\033[1;31m"
CYAN  = "\033[1;36m"
GRAY  = "\033[0;37m"

class ResultParser:
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
        found  = data.get("found", False)
        error  = data.get("error", "")

        if error:
            return f"{RED}[!] ERROR: {error}{RESET}"

        color = STATUS_COLORS.get(status, GRAY)

        if rtype == "dir":
            if found:
                return f"{GREEN}[+] FOUND: {result} ({color}{status}{RESET}{GREEN}){RESET}"
            return f"{GRAY}[-] NOT FOUND: {result}{RESET}"

        if rtype == "endpoint":
            if found:
                return f"{GREEN}[+] ENDPOINT: {result} ({color}{status}{RESET}{GREEN}){RESET}"
            return f"{GRAY}[-] NOT FOUND: {result}{RESET}"

        if rtype == "user":
            if found:
                return f"{GREEN}[+] VALID USER: {result}{RESET}"
            return f"{GRAY}[-] INVALID: {result}{RESET}"

        if rtype == "email":
            if found:
                return f"{GREEN}[+] VALID EMAIL: {result}{RESET}"
            return f"{GRAY}[-] INVALID: {result}{RESET}"

        if rtype == "progress":
            total   = data.get("total", 0)
            current = data.get("current", 0)
            pct     = (current / total * 100) if total > 0 else 0
            sys.stdout.write(f"\r{CYAN}[~] Progress: {current}/{total} ({pct:.1f}%){RESET}   ")
            sys.stdout.flush()
            return None

        if rtype == "summary":
            found_count = data.get("found_count", 0)
            total       = data.get("total", 0)
            elapsed     = data.get("elapsed_ms", 0)
            return (
                f"\n{CYAN}[*] Scan complete — "
                f"{found_count} found / {total} tested in {elapsed}ms{RESET}"
            )

        return None

    def print_result(self, data: dict):
        line = self.format_result(data)
        if line:
            print(line)
