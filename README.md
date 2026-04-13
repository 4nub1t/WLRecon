# WLRecon — Wordlist Recon Framework

```
 ██╗    ██╗██╗     ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██║    ██║██║     ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██║ █╗ ██║██║     ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██║███╗██║██║     ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ╚███╔███╔╝███████╗██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
  Wordlist Recon Framework  |  made by 4nub1t  |  v1.0.0
```

> **For authorized penetration testing, CTFs, labs (TryHackMe, HackTheBox, OSCP), and educational use only.**

---

## Description

WLRecon is a high-performance, modular, hybrid reconnaissance framework designed for web application penetration testing, OSCP-style lab environments, and red team reconnaissance workflows.

It is **not a script**. It is a two-layer architecture:

- **Python Orchestration Layer** — CLI interface, user interaction, configuration, output formatting, module coordination.
- **Go High-Performance Engine** — all HTTP fuzzing and enumeration, goroutine-based concurrency, structured JSON output.

---

## Architecture

```
WLRecon/
├── python/                   # Orchestration layer
│   ├── main.py               # Entry point
│   ├── cli.py                # Interactive menu, banner, user flow
│   ├── config.py             # Configuration manager
│   ├── parser.py             # JSON result parser + terminal formatter
│   └── modules/
│       ├── email_enum.py     # Email enumeration module
│       ├── user_enum.py      # Username enumeration module
│       ├── dir_enum.py       # Directory bruteforce module
│       └── endpoint_enum.py  # API endpoint discovery module
│
├── go-engine/                # High-performance engine
│   ├── main.go               # CLI flags, entry point
│   ├── engine.go             # Core engine, worker pool, wordlist loader
│   ├── http.go               # HTTP client with proxy and timeout support
│   └── worker.go             # Mode-specific probe logic (dir/endpoint/user/email)
│
├── output/                   # Scan output directory
├── wordlists/                # Place your wordlists here
├── README.md
├── requirements.txt
├── go.mod
└── .gitignore
```

**Communication:**  
The Go engine outputs NDJSON (newline-delimited JSON) to stdout. Python reads it line by line via subprocess and formats it for the terminal.

```
Go Engine  ──NDJSON──►  Python Parser  ──formatted──►  Terminal
```

---

## Requirements

- Python 3.11+
- Go 1.22+
- A wordlist (e.g. `/usr/share/wordlists/dirb/common.txt`, SecLists)

---

## Installation

```bash
git clone https://github.com/4nub1t/wlrecon.git
cd wlrecon
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
> On Windows: use `venv\Scripts\activate` instead.

---

## Build the Go Engine

```bash
cd go-engine
go build -o wlrecon-engine .
cd ..
```

On Windows:
```powershell
cd go-engine
go build -o wlrecon-engine.exe .
cd ..
```

---

## Usage

```bash
python python/main.py
```
> **Note:** Activate the virtual environment before running:
> ```bash
> source venv/bin/activate
> ```

The interactive menu will appear:

```
  ┌─────────────────────────────────────┐
  │           SELECT MODULE             │
  ├─────────────────────────────────────┤
  │  [1]  Email Enumeration             │
  │  [2]  Username Enumeration          │
  │  [3]  Directory Bruteforce          │
  │  [4]  Endpoint Discovery            │
  │  [0]  Exit                          │
  └─────────────────────────────────────┘
```

Then provide:
- **Target URL** — full URL (e.g. `http://10.10.10.10` or `http://10.10.10.10/login`)
- **Wordlist path** — absolute or relative path to your wordlist
- **Threads** — concurrency (default: 50)
- **Proxy** — optional Burp Suite or custom proxy
- **Timeout** — HTTP timeout in seconds (default: 10)

---

## Module Guide

### [1] Email Enumeration
**Target:** The password reset or login endpoint accepting an `email` parameter.  
**Example target:** `http://10.10.10.10/forgot-password`  
**Wordlist:** Usernames or email prefixes. WLRecon will append `@<target-domain>` automatically if no `@` is present.

### [2] Username Enumeration
**Target:** The login form endpoint accepting a `username` parameter.  
**Example target:** `http://10.10.10.10/login`  
**Detection heuristic:** Response codes differ between valid and invalid users (e.g. 200 vs 404). Tune based on target behaviour.

### [3] Directory Bruteforce
**Target:** Root of the web application.  
**Example target:** `http://10.10.10.10`  
**Hit criteria:** HTTP 200, 201, 204, 301, 302, 307, 308, 401, 403.

### [4] Endpoint Discovery
**Target:** Base URL. Paths are probed under `/api/<word>`.  
**Example target:** `http://10.10.10.10`

---

## Output Format

```
[+] FOUND: /admin (200)
[+] FOUND: /uploads (403)
[+] VALID USER: admin
[+] VALID EMAIL: admin@target.local
[-] NOT FOUND: /secret
[~] Progress: 400/2000 (20.0%)
[*] Scan complete — 3 found / 2000 tested in 4821ms
```

---

## Proxy Usage (Burp Suite Integration)

1. Start Burp Suite and confirm the proxy listener is active (default: `127.0.0.1:8080`).
2. When prompted for proxy, enter:
   ```
   http://127.0.0.1:8080
   ```
3. All HTTP requests from the Go engine will route through Burp.
4. To intercept only specific requests, configure Burp scope before running.

> **Note:** For HTTPS targets with Burp, install the Burp CA certificate in your system trust store and ensure the Go engine trusts it, or disable TLS verification (not recommended in production).

---

## JSON Communication Protocol

The Go engine writes NDJSON to stdout. Each line is one of:

```json
{"type":"dir","result":"/admin","status":200,"found":true}
{"type":"user","result":"admin","status":200,"found":true}
{"type":"email","result":"test@target.local","status":200,"found":true}
{"type":"progress","total":2000,"current":100}
{"type":"summary","total":2000,"found_count":3,"elapsed_ms":4821}
{"type":"dir","result":"/secret","status":404,"found":false}
{"error":"connection refused"}
```

Python parses each JSON line and applies ANSI-colored formatting.

---

## Why WLRecon

Most recon tools are black boxes. WLRecon was built during OSCP preparation
to understand and replicate the internal logic of tools like ffuf and gobuster —
not to replace them.

**What it demonstrates:**
- Systems architecture: separating concerns across two languages
- Go concurrency: goroutines, worker pools, atomic counters
- Python tooling: subprocess orchestration, real-time JSON parsing
- Red team mindset: modular design built for extensibility

---

## Limitations

- Username/email enumeration accuracy depends on the target's HTTP response behaviour. There is no universal heuristic — tune per target.
- Endpoint discovery uses `/api/<word>` prefix by default. For custom paths, modify `worker.go` `probeEndpoint()`.
- No HTTPS certificate verification bypass is implemented by default (intentional for safety).
- Rate limiting or WAFs on the target may reduce accuracy. Use lower thread counts and add delays if needed.
- No built-in output-to-file feature yet (pipe stdout to a file if needed).

---

## Future Improvements

- [ ] Output to file (`-output result.txt`)
- [ ] Custom status code filter (`-fc 404,400`)
- [ ] Response size/word/line-based filtering (like ffuf)
- [ ] HTTPS with custom CA / TLS skip flag
- [ ] Custom HTTP headers support
- [ ] Rate limiting with configurable delay between requests
- [ ] Recursive directory bruteforce
- [ ] Follow-redirect toggle
- [ ] JSON report export for documentation

---

## Author

**4nub1t** — Red Team / Offensive Security  
eJPTv2 certified | OSCP preparation | CTF competitor  
[GitHub](https://github.com/4nub1t)

---

## Disclaimer

> WLRecon is developed for **authorized penetration testing**, **CTF competitions**, **educational labs** (TryHackMe, HackTheBox, OSCP), and **controlled security research environments only**.
>
> Using this tool against systems without explicit written permission from the system owner is **illegal** under computer crime laws in most jurisdictions (CFAA, Computer Misuse Act, etc.).
>
> The author assumes **no responsibility or liability** for any misuse, damage, or legal consequences arising from the use of this tool outside of authorized contexts.
>
> **You are solely responsible for ensuring you have legal authorization before running any scan.**
