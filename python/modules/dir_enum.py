import os
import subprocess
import threading
from datetime import datetime


class DirEnumerator:
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
        mode_map    = {
            "DirEnumerator":      "dir",
            "EndpointEnumerator": "endpoint",
            "UserEnumerator":     "user",
            "EmailEnumerator":    "email",
        }
        mode = mode_map.get(self.__class__.__name__, "dir")

        os.makedirs(output_dir, exist_ok=True)

        if not output_file:
            output_file = datetime.now().strftime("wlrecon_%Y%m%d_%H%M%S")

        filepath = os.path.join(output_dir, f"{output_file}.{fmt}")
        self.parser.configure_output(filepath, fmt, {
            "target":   self.config.get("target"),
            "wordlist": self.config.get("wordlist"),
            "mode":     mode,
        })

    def _build_cmd(self):
        mode_map = {
            "DirEnumerator":      "dir",
            "EndpointEnumerator": "endpoint",
            "UserEnumerator":     "user",
            "EmailEnumerator":    "email",
        }
        mode = mode_map.get(self.__class__.__name__, "dir")

        cmd = [
            self.config.get("engine_path"),
            "-mode",     mode,
            "-target",   self.config.get("target"),
            "-wordlist", self.config.get("wordlist"),
            "-threads",  str(self.config.get("threads")),  
            "-timeout",  str(self.config.get("timeout")),   
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

        if self.config.get("recursive") and mode in ("dir", "endpoint"):
            cmd += [
                "-recursive",
                "-depth",        str(self.config.get("max_depth", 3)),          
                "-max-recurse",  str(self.config.get("max_recurse_per_level", 30)),  
            ]

        return cmd

    def _invoke(self, cmd):
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stderr_lines = []
            def drain_stderr():
                for line in proc.stderr:
                    stderr_lines.append(line)
            t = threading.Thread(target=drain_stderr, daemon=True)
            t.start()

            for line in proc.stdout:
                data = self.parser.parse_line(line)
                if data:
                    self.parser.print_result(data)

            proc.wait()
            t.join()

            if proc.returncode != 0 and stderr_lines:
                err = "".join(stderr_lines).strip()
                print(f"\033[1;31m[!] Engine error: {err}\033[0m")

        except FileNotFoundError:
            print(f"\033[1;31m[!] Engine binary not found. Build it first.\033[0m")
        except KeyboardInterrupt:
            proc.terminate()
            proc.wait()  
            print(f"\n\033[1;33m[!] Scan interrupted.\033[0m")
