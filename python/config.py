import os

class Config:
    def __init__(self):
        self._data = {
            "target": "",
            "wordlist": "",
            "threads": "50",
            "proxy": "",
            "timeout": "10",
            "match_string": "",
            "invalid_string": "",
            "extra_headers": "",
            "extra_params": "",
            "tls_skip": False,
            "recursive": False,
            "max_depth": "3",
            "output_file": "",
            "output_format": "txt",
            "engine_path": os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "go-engine",
                "wlrecon-engine"
            ),
            "output_dir": os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "output"
            ),
        }

    def set(self, key: str, value):
        self._data[key] = value

    def get(self, key: str, fallback=None):
        return self._data.get(key, fallback)

    def validate(self) -> tuple[bool, str]:
        if not self._data.get("target"):
            return False, "Target URL is required."
        if not self._data.get("wordlist"):
            return False, "Wordlist path is required."
        if not os.path.isfile(self._data.get("wordlist", "")):
            return False, f"Wordlist not found: {self._data['wordlist']}"
        engine = self._data.get("engine_path", "")
        if not os.path.isfile(engine):
            return False, f"Go engine binary not found at: {engine}\nRun: cd go-engine && go build -o wlrecon-engine ."
        return True, ""
