package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type EngineConfig struct {
	Mode     string
	Target   string
	Wordlist string
	Threads  int
	Timeout  int
	Proxy    string
}

type Result struct {
	Type      string `json:"type"`
	Result    string `json:"result"`
	Status    int    `json:"status,omitempty"`
	Found     bool   `json:"found"`
	Error     string `json:"error,omitempty"`
}

type ProgressResult struct {
	Type    string `json:"type"`
	Total   int    `json:"total"`
	Current int64  `json:"current"`
}

type SummaryResult struct {
	Type       string `json:"type"`
	Total      int    `json:"total"`
	FoundCount int64  `json:"found_count"`
	ElapsedMs  int64  `json:"elapsed_ms"`
}

type Engine struct {
	cfg    EngineConfig
	client *HTTPClient
	output chan interface{}
	mu     sync.Mutex
}

func NewEngine(cfg EngineConfig) *Engine {
	return &Engine{
		cfg:    cfg,
		client: NewHTTPClient(cfg.Timeout, cfg.Proxy),
		output: make(chan interface{}, 512),
	}
}

func (e *Engine) Run() error {
	words, err := loadWordlist(e.cfg.Wordlist)
	if err != nil {
		return fmt.Errorf("loading wordlist: %w", err)
	}

	total      := len(words)
	var counter atomic.Int64
	var found   atomic.Int64
	start       := time.Now()

	jobs := make(chan string, e.cfg.Threads*2)
	var wg sync.WaitGroup

	go e.emitOutputs()

	for i := 0; i < e.cfg.Threads; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for word := range jobs {
				result := e.process(word)
				counter.Add(1)
				if result.Found {
					found.Add(1)
				}
				e.output <- result

				cur := counter.Load()
				if cur%100 == 0 || int(cur) == total {
					e.output <- ProgressResult{
						Type:    "progress",
						Total:   total,
						Current: cur,
					}
				}
			}
		}()
	}

	for _, w := range words {
		jobs <- w
	}
	close(jobs)
	wg.Wait()

	e.output <- SummaryResult{
		Type:       "summary",
		Total:      total,
		FoundCount: found.Load(),
		ElapsedMs:  time.Since(start).Milliseconds(),
	}

	close(e.output)
	return nil
}

func (e *Engine) process(word string) Result {
	word = strings.TrimSpace(word)
	if word == "" || strings.HasPrefix(word, "#") {
		return Result{Type: e.cfg.Mode, Result: word, Found: false}
	}

	switch e.cfg.Mode {
	case "dir":
		return e.probeDir(word)
	case "endpoint":
		return e.probeEndpoint(word)
	case "user":
		return e.probeUser(word)
	case "email":
		return e.probeEmail(word)
	default:
		return Result{Type: e.cfg.Mode, Error: "unknown mode: " + e.cfg.Mode}
	}
}

func (e *Engine) emitOutputs() {
	enc := json.NewEncoder(os.Stdout)
	for item := range e.output {
		_ = enc.Encode(item)
	}
}

func loadWordlist(path string) ([]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var words []string
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" && !strings.HasPrefix(line, "#") {
			words = append(words, line)
		}
	}
	return words, scanner.Err()
}
