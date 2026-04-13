import json
import sys
import csv
import xml.etree.ElementTree as ET
from datetime import datetime

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
        self._output_file: str = ""
        self._output_format: str = "txt"
        self._meta: dict = {}

    def configure_output(self, filepath: str, fmt: str, meta: dict):
        self._hits = []
        self._output_file = filepath
        self._output_format = fmt.lower()
        self._meta = meta

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
        depth  = data.get("depth", 0)

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
        depth_str  = f" {GRAY}(depth:{depth}){RESET}" if depth > 0 else ""

        if rtype == "dir":
            return f"{GREEN}[+] FOUND:       {result}{RESET}{GRAY}  {color}{status}{RESET}{GRAY}{length_str}{RESET}{depth_str}"
        if rtype == "endpoint":
            return f"{GREEN}[+] ENDPOINT:    {result}{RESET}{GRAY}  {color}{status}{RESET}{GRAY}{length_str}{RESET}{depth_str}"
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
        total       = data.get("total", 0)
        found_count = data.get("found_count", 0)
        elapsed     = data.get("elapsed_ms", 0)

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
                    depth  = hit.get("depth", 0)
                    color  = STATUS_COLORS.get(status, GRAY)
                    depth_str = f"  {GRAY}depth:{depth}{RESET}" if depth > 0 else ""
                    print(f"  {GREEN}>{RESET} {result:<35} {color}{status}{RESET}  {GRAY}[{length}b]{RESET}{depth_str}")

        print(f"\n{CYAN}{'─' * 55}{RESET}")
        print(f"  {GRAY}Tested:{RESET} {total}   {GRAY}Found:{RESET} {GREEN}{found_count}{RESET}   {GRAY}Time:{RESET} {elapsed}ms")
        print(f"{CYAN}{'─' * 55}{RESET}\n")

        print(f"DEBUG _output_file='{self._output_file}' hits={len(self._hits)}")
        if self._output_file:
            self._save_output(total, found_count, elapsed)

        if self._output_file:
            self._save_output(total, found_count, elapsed)

    def _save_output(self, total: int, found_count: int, elapsed: int):
        if not self._output_file:                                           
            print(f"{RED}[!] Output path not configured — file not saved.{RESET}") 
            return  
        fmt = self._output_format
        try:
            if fmt == "txt":
                self._save_txt(total, found_count, elapsed)
            elif fmt == "json":
                self._save_json(total, found_count, elapsed)
            elif fmt == "csv":
                self._save_csv()
            elif fmt == "xml":
                self._save_xml(total, found_count, elapsed)
            print(f"{CYAN}[*] Output saved to: {self._output_file}{RESET}")
        except Exception as ex:
            print(f"{RED}[!] Failed to save output: {ex}{RESET}")

    def _save_txt(self, total, found_count, elapsed):
        with open(self._output_file, "w") as f:
            f.write("=" * 55 + "\n")
            f.write("  WLRecon Scan Report\n")
            f.write(f"  Date     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"  Target   : {self._meta.get('target', '')}\n")
            f.write(f"  Wordlist : {self._meta.get('wordlist', '')}\n")
            f.write(f"  Mode     : {self._meta.get('mode', '')}\n")
            f.write("=" * 55 + "\n\n")

            labels = {"dir": "DIRECTORIES / PATHS", "endpoint": "ENDPOINTS",
                      "user": "VALID USERS", "email": "VALID EMAILS"}
            type_groups: dict[str, list[dict]] = {}
            for hit in self._hits:
                type_groups.setdefault(hit.get("type", "unknown"), []).append(hit)

            for rtype, hits in type_groups.items():
                f.write(f"{labels.get(rtype, rtype.upper())} ({len(hits)})\n")
                f.write("-" * 45 + "\n")
                for hit in hits:
                    result    = str(hit.get("result", ""))
                    status    = hit.get("status", 0)
                    length    = hit.get("length", 0)
                    depth     = hit.get("depth", 0)
                    depth_str = f"  depth:{depth}" if depth > 0 else ""
                    f.write(f"  {result:<35} {status}  [{length}b]{depth_str}\n")
                f.write("\n")
            f.write("-" * 55 + "\n")
            f.write(f"  Tested: {total}   Found: {found_count}   Time: {elapsed}ms\n")
            f.write("-" * 55 + "\n")

    def _save_json(self, total, found_count, elapsed):
        report = {
            "meta": {
                "date": datetime.now().isoformat(),
                "target": self._meta.get("target", ""),
                "wordlist": self._meta.get("wordlist", ""),
                "mode": self._meta.get("mode", ""),
                "total_tested": total,
                "found_count": found_count,
                "elapsed_ms": elapsed,
            },
            "results": self._hits,
        }
        with open(self._output_file, "w") as f:
            json.dump(report, f, indent=2)

    def _save_csv(self):
        with open(self._output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["type", "result", "status", "length", "depth", "found"])
            writer.writeheader()
            for hit in self._hits:
                writer.writerow({
                    "type":   hit.get("type", ""),
                    "result": str(hit.get("result", "")), 
                    "status": hit.get("status", 0),
                    "length": hit.get("length", 0),
                    "depth":  hit.get("depth", 0),
                    "found":  hit.get("found", True),
                })

    def _save_xml(self, total, found_count, elapsed):
        root = ET.Element("wlrecon")
        meta = ET.SubElement(root, "meta")
        ET.SubElement(meta, "date").text     = datetime.now().isoformat()
        ET.SubElement(meta, "target").text   = self._meta.get("target", "")
        ET.SubElement(meta, "wordlist").text = self._meta.get("wordlist", "")
        ET.SubElement(meta, "mode").text     = self._meta.get("mode", "")
        ET.SubElement(meta, "total").text    = str(total)
        ET.SubElement(meta, "found").text    = str(found_count)
        ET.SubElement(meta, "elapsed_ms").text = str(elapsed)

        results = ET.SubElement(root, "results")
        for hit in self._hits:
            item = ET.SubElement(results, "item")
            ET.SubElement(item, "type").text   = hit.get("type", "")
            ET.SubElement(item, "result").text = str(hit.get("result", ""))
            ET.SubElement(item, "status").text = str(hit.get("status", 0))
            ET.SubElement(item, "length").text = str(hit.get("length", 0))
            ET.SubElement(item, "depth").text  = str(hit.get("depth", 0))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(self._output_file, encoding="unicode", xml_declaration=True)
