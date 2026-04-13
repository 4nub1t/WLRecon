package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	mode     := flag.String("mode", "", "Scan mode: dir | endpoint | user | email")
	target   := flag.String("target", "", "Target URL")
	wordlist := flag.String("wordlist", "", "Path to wordlist")
	threads  := flag.Int("threads", 50, "Number of concurrent goroutines")
	timeout  := flag.Int("timeout", 10, "HTTP timeout in seconds")
	proxy    := flag.String("proxy", "", "Proxy URL (e.g. http://127.0.0.1:8080)")

	flag.Parse()

	if *mode == "" || *target == "" || *wordlist == "" {
		fmt.Fprintln(os.Stderr, "usage: wlrecon-engine -mode <dir|endpoint|user|email> -target <url> -wordlist <path> [-threads N] [-timeout N] [-proxy url]")
		os.Exit(1)
	}

	cfg := EngineConfig{
		Mode:     *mode,
		Target:   *target,
		Wordlist: *wordlist,
		Threads:  *threads,
		Timeout:  *timeout,
		Proxy:    *proxy,
	}

	engine := NewEngine(cfg)
	if err := engine.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "engine error: %v\n", err)
		os.Exit(1)
	}
}
