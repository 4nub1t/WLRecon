import os
import subprocess
from datetime import datetime

class UserEnumerator:
    def __init__(self, config, parser):
        self.config = config
        self.parser = parser

    def run(self):
        ok, err = self.config.validate()
        if not ok:
            print(f"\033[1;31m[!] {err}\033[0m")
            return

        self._setup_output()
        self._invoke(self._build_cmd())

    def _setup_output(self):
        output_dir  = self.config.get("output_dir")
        output_file = self.config.get("output_file", "").strip()
        fmt         = self.config.get("output_format", "txt").strip().lower()

        os.makedirs(output_dir, exist_ok=True)

        if not output_file:
            output_file = datetime.now().strftime("wlrecon_%Y%m%d_%H%M%S")

        filepath = os.path.join(output_dir, f"{output_file}.{fmt}")
        self.parser.configure_output(filepath, fmt, {
            "target":   self.config.get("target"),
            "wordlist": self.config.get("wordlist"),
            "mode":     "user",
        })

    def _build_cmd(self) -> list[str]:
        cmd = [
            self.config.get("engine_path"),
            "-mode", "user",
            "-target", self.config.get("target"),
            "-wordlist", self.config.get("wordlist"),
            "-threads", self.config.get("threads"),
            "-timeout", self.config.get("timeout"),
        ]
        if self.config.get("proxy"):
            cmd += ["-proxy", self.config.get("proxy")]
        if self.config.get("match_string"):
            cmd += ["-match-string", self.config.get("match_string")]
        if self.config.get("invalid_string"):
            cmd += ["-invalid-string", self.config.get("invalid_string")]
        if self.config.get("extra_headers"):
            cmd += ["-headers", self.config.get("extra_headers")]
        if self.config.get("extra_params"):
            cmd += ["-params", self.config.get("extra_params")]
        if self.config.get("tls_skip"):
            cmd += ["-tls-skip"]
        return cmd

    def _invoke(self, cmd: list[str]):
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in proc.stdout:
                data = self.parser.parse_line(line)
                if data:
                    self.parser.print_result(data)
            proc.wait()
            if proc.returncode != 0:
                err = proc.stderr.read()
                if err:
                    print(f"\033[1;31m[!] Engine error: {err.strip()}\033[0m")
        except FileNotFoundError:
            print(f"\033[1;31m[!] Engine binary not found. Build it first.\033[0m")
        except KeyboardInterrupt:
            proc.terminate()
            print("\n\033[1;33m[!] Scan interrupted.\033[0m")
