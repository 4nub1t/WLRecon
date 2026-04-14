# WLRecon — Wordlist Recon Framework

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Go](https://img.shields.io/badge/Go-1.22+-00ADD8)
![License](https://img.shields.io/badge/Use-Authorized%20Only-red)
![Status](https://img.shields.io/badge/Status-Active-success)

```
 ██╗    ██╗██╗     ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██║    ██║██║     ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██║ █╗ ██║██║     ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██║███╗██║██║     ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ╚███╔███╔╝███████╗██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
  Wordlist Recon Framework  |  made by 4nub1t  |  v1.1.0
```

> **For authorized penetration testing, CTFs, labs (TryHackMe, HackTheBox, OSCP), and educational use only.**

---

## Description

WLRecon is a high-performance, modular, hybrid reconnaissance framework designed for web application penetration testing, OSCP-style lab environments, and red team reconnaissance workflows.

It is **not a script**. It is a two-layer architecture:

- **Python Orchestration Layer** — CLI interface, user interaction, configuration, output formatting, module coordination.
- **Go High-Performance Engine** — all HTTP/HTTPS fuzzing and enumeration, goroutine-based concurrency, structured JSON output.

---

## Why WLRecon?

Unlike traditional tools, WLRecon provides:

- High-performance concurrent fuzzing (Go goroutines)
- Real-time streaming results via NDJSON
- Intelligent detection for dynamic applications
- Modular architecture for multiple recon techniques
- Recursive scanning with depth tracking
- Proxy support (Burp Suite integration)
- Multi-format output (txt, json, csv, xml)

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
pip install -r requirements.txt
```

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
- **Target URL**
  Full target endpoint (e.g. `http://10.10.10.10` or `http://10.10.10.10/login`)

- **Wordlist**
  Path to wordlist file (local or absolute path supported)

- **Threads**
  Number of concurrent workers (default: `50`)

- **Proxy (optional)**
  HTTP proxy for traffic routing (e.g. Burp Suite `http://127.0.0.1:8080`)

- **Timeout**
  Request timeout in seconds (default: `10`)

- **TLS Verification**
  Skip TLS certificate verification for HTTPS targets (default: `false`)

- **Recursive Scan**
  Enable recursive enumeration of discovered directories/endpoints (default: `false`)

- **Max Depth**
  Maximum recursion depth (only applies if Recursive Scan is enabled) (default: `3`)

- **Output Format**
  Output format for results (`txt`, `json`, `csv`, `xml`) (default: `txt`)

- **Output Filename**
  Custom filename for saved results (default: `wlrecon_<timestamp>`)

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
**Target:** Base URL. Endpoints are discovered by probing under `/api/<word>` by default (configurable in `worker.go`).  
**Example target:** `http://10.10.10.10`

---

## Advanced Detection Mode

By default WLRecon uses **baseline auto-detection** — it probes the target with a guaranteed-invalid word and compares all subsequent responses against that baseline (status code + response length).

For targets that always return HTTP 200 with error messages in the response body (common in CTF labs and custom login forms), use the string-based detection options:

### `match-string`
Mark a result as **FOUND** if the response body contains this string.

```bash
match-string: Welcome back
```

Use when the server returns a known string only for valid results.

### `invalid-string`
Mark a result as **NOT FOUND** if the response body contains this string.

```bash
invalid-string: Email does not exist
```

Use when the server returns a known error string for invalid entries — WLRecon marks everything else as valid.

### `extra-headers`
Comma-separated list of additional HTTP headers. Useful for targets requiring `X-Requested-With`, `Referer`, or custom auth headers.

```bash
extra-headers: X-Requested-With:XMLHttpRequest,Referer:http://10.10.10.10/login
```

### `extra-params`
Additional POST parameters appended to the request body. Useful for endpoints requiring extra fields like `function=login`.

```bash
extra-params: function=login
```

---

## TLS Options

WLRecon now supports skipping TLS certificate verification when targeting HTTPS services with self-signed or invalid certificates.

Prompt

```bash
Skip TLS verification? [y/N]
```
**Use cases**
- OSCP labs
- HackTheBox / TryHackMe environments
- Internal staging environments
- Self-signed certificates

---

## Recursive Scanning

Directory and endpoint enumeration modules now support automatic recursive scanning of discovered paths.

Prompt

```bash
Enable recursive scan? [y/N]
Max depth [3]
```

**Behavior**
- Recursion is triggered on valid discovered directories/endpoints
- Each recursion level increases scan depth
- Results include depth annotation

Output format

```bash
/admin
/admin/login (depth:1)
/admin/panel (depth:2)
```

**Supported modules**
- Directory Bruteforce
- Endpoint Discovery
  
**Not supported**
- Username enumeration
- Email enumeration

---

## Output

WLRecon automatically saves scan results to the output/ directory upon completion.

Prompt

```bash
Format [txt/json/csv/xml]
Output filename [wlrecon_<timestamp>]
```

**Behavior**
- Default filename: wlrecon_<timestamp>
- Extension is appended automatically based on selected format
- Output location: ./output/

### Example: TXT output

```bash

Example: TXT output

```bash
DIRECTORIES / PATHS
--------------------
/admin        200
/login        302
/phpmyadmin   403
```

### Example: JSON output

```json
{
  "meta": {
    "target": "http://example.com",
    "mode": "dir",
    "total_tested": 1000,
    "found_count": 12,
    "elapsed_ms": 4200
  },
  "results": [
    {
      "type": "dir",
      "result": "/admin",
      "status": 200,
      "found": true
    }
  ]
}
```

---

## Example — Recursive Directory Bruteforce with Output

### Target: http://192.168.1.150

```bash
[*] Target Configuration
    Target URL          : http://192.168.1.150
    Wordlist path       : /usr/share/wordlists/dirb/common.txt
    Threads [50]        : 40
    Proxy [skip]        :
    Timeout secs [10]   : 8

[*] Detection Options
    match-string  [skip]:
    invalid-string[skip]:

[*] Advanced Options
    Extra headers :
    Extra params  :

[*] HTTPS Options
    Skip TLS verification? [y/N]: N

[*] Recursive Options
    Enable recursive scan? [y/N]: y
    Max depth [3]       : 2

[*] Output Options
    Format [txt/json/csv/xml] (default: txt): json
    Output filename [wlrecon_20260413_230000]: internal_scan

[*] Starting module...

[+] FOUND:       /admin              200 [1452b]
[+] FOUND:       /login              302 [512b]
[+] FOUND:       /backup             403 [298b]
[+] FOUND:       /api                200 [2048b]
[+] FOUND:       /admin/panel        200 [5321b] (depth:1)
[+] FOUND:       /admin/config       403 [301b]  (depth:1)
[+] FOUND:       /api/v1             200 [4123b] (depth:1)
[+] FOUND:       /api/v1/users       200 [6123b] (depth:2)

[~] Progress: 5230/5230 (100.0%)

-------------------------------------------------------
  SCAN RESULTS SUMMARY
-------------------------------------------------------

  DIRECTORIES / PATHS (8)
  -----------------------------------------------------
  > /admin                             200  [1452b]
  > /login                             302  [512b]
  > /backup                            403  [298b]
  > /api                               200  [2048b]
  > /admin/panel                       200  [5321b]  depth:1
  > /admin/config                      403  [301b]   depth:1
  > /api/v1                            200  [4123b]  depth:1
  > /api/v1/users                      200  [6123b]  depth:2

-------------------------------------------------------
  Tested: 5230   Found: 8   Time: 8421ms
-------------------------------------------------------

[*] Output saved to: ./output/internal_scan.json
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

## Limitations

- Accuracy depends on target HTTP response behavior
- Endpoint discovery uses /api/<word> pattern by default
- Recursive scanning only applies to directory and endpoint modules
- WAF/rate limiting may reduce scan effectiveness

---

## Future Improvements

- [ ] Status code filtering (include/exclude codes)
- [ ] Response size filtering (bytes, words, lines)
- [ ] Rate limiting with delay between requests
- [ ] Follow-redirect toggle
- [ ] Advanced WAF evasion techniques

---

## Author

**4nub1t** — Red Team / Offensive Security  
eJPTv2 certified | OSCP preparation | CTF competitor  
[GitHub](https://github.com/4nub1t)

---

## Disclaimer

> WLRecon is developed for **authorized penetration testing**, **CTF competitions**, **educational labs** (TryHackMe, HackTheBox, OSCP), and **controlled security research environments only**.
>
> Using this tool against systems without **explicit written permission** from the system owner is **illegal** under computer crime laws in most jurisdictions (e.g. CFAA, Computer Misuse Act).
>
> The author assumes **no responsibility or liability** for any misuse, damage, or legal consequences arising from the use of this tool.

### By using WLRecon, you agree that:

- you have proper authorization before testing any target  
- you understand and comply with applicable laws and regulations  
- you take full responsibility for your actions  

**Use responsibly.**

---
-------------------------------------------------------

