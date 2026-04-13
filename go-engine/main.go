package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	mode          := flag.String("mode", "", "Scan mode: dir | endpoint | user | email")
	target        := flag.String("target", "", "Target URL")
	wordlist      := flag.String("wordlist", "", "Path to wordlist")
	threads       := flag.Int("threads", 50, "Number of concurrent goroutines")
	timeout       := flag.Int("timeout", 10, "HTTP timeout in seconds")
	proxy         := flag.String("proxy", "", "Proxy URL (e.g. http://127.0.0.1:8080)")
	matchString   := flag.String("match-string", "", "Mark as FOUND if response body contains this string")
	invalidString := flag.String("invalid-string", "", "Mark as NOT FOUND if response body contains this string")
	extraHeaders  := flag.String("headers", "", "Extra headers in format 'Key1:Value1,Key2:Value2'")
	extraParams   := flag.String("params", "", "Extra POST params in format 'key1=value1&key2=value2'")

	flag.Parse()

	if *mode == "" || *target == "" || *wordlist == "" {
		fmt.Fprintln(os.Stderr, "usage: wlrecon-engine -mode <dir|endpoint|user|email> -target <url> -wordlist <path> [-threads N] [-timeout N] [-proxy url] [-match-string str] [-invalid-string str] [-headers 'K:V,...'] [-params 'k=v&...']")
		os.Exit(1)
	}

	cfg := EngineConfig{
		Mode:          *mode,
		Target:        *target,
		Wordlist:      *wordlist,
		Threads:       *threads,
		Timeout:       *timeout,
		Proxy:         *proxy,
		MatchString:   *matchString,
		InvalidString: *invalidString,
		ExtraHeaders:  *extraHeaders,
		ExtraParams:   *extraParams,
	}

	engine := NewEngine(cfg)
	if err := engine.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "engine error: %v\n", err)
		os.Exit(1)
	}
}
