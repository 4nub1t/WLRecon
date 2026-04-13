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
	Mode          string
	Target        string
	Wordlist      string
	Threads       int
	Timeout       int
	Proxy         string
	MatchString   string
	InvalidString string
	ExtraHeaders  string
	ExtraParams   string
	TLSSkip       bool
	Recursive     bool
	MaxDepth      int
}

type Result struct {
	Type   string `json:"type"`
	Result string `json:"result"`
	Status int    `json:"status,omitempty"`
	Length int64  `json:"length,omitempty"`
	Found  bool   `json:"found"`
	Depth  int    `json:"depth,omitempty"`
	Error  string `json:"error,omitempty"`
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

type BaselineResponse struct {
	Status int
	Length int64
	Body   string
}

type Engine struct {
	cfg      EngineConfig
	client   *HTTPClient
	output   chan interface{}
	baseline BaselineResponse
	visited  map[string]bool
	mu       sync.Mutex
}

func NewEngine(cfg EngineConfig) *Engine {
	return &Engine{
		cfg:     cfg,
		client:  NewHTTPClient(cfg.Timeout, cfg.Proxy, cfg.ExtraHeaders, cfg.TLSSkip),
		output:  make(chan interface{}, 512),
		visited: make(map[string]bool),
	}
}

func (e *Engine) Run() error {
	words, err := loadWordlist(e.cfg.Wordlist)
	if err != nil {
		return fmt.Errorf("loading wordlist: %w", err)
	}

	baseline, err := e.calibrate(e.cfg.Target)
	if err != nil {
		baseline = BaselineResponse{Status: 404, Length: -1, Body: ""}
	}
	e.baseline = baseline

	start := time.Now()
	total, found := e.scanTarget(e.cfg.Target, words, 0)

	e.output <- SummaryResult{
		Type:       "summary",
		Total:      total,
		FoundCount: found,
		ElapsedMs:  time.Since(start).Milliseconds(),
	}

	close(e.output)
	return nil
}

func (e *Engine) scanTarget(target string, words []string, depth int) (int, int64) {
	e.mu.Lock()
	if e.visited[target] {
		e.mu.Unlock()
		return 0, 0
	}
	e.visited[target] = true
	e.mu.Unlock()

	total := len(words)
	var counter atomic.Int64
	var found atomic.Int64

	jobs := make(chan string, e.cfg.Threads*2)
	var wg sync.WaitGroup
	var recurseTargets []string
	var recurseMu sync.Mutex

	for i := 0; i < e.cfg.Threads; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for word := range jobs {
				result := e.processAt(target, word, depth)
				counter.Add(1)
				if result.Found {
					found.Add(1)
					if e.cfg.Recursive && depth < e.cfg.MaxDepth {
						if isRecursable(result.Status) {
							newTarget := strings.TrimRight(target, "/") + result.Result
							recurseMu.Lock()
							recurseTargets = append(recurseTargets, newTarget)
							recurseMu.Unlock()
						}
					}
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

	for _, subTarget := range recurseTargets {
		subTotal, subFound := e.scanTarget(subTarget, words, depth+1)
		total += subTotal
		found.Add(subFound)
	}

	return total, found.Load()
}

func isRecursable(status int) bool {
	switch status {
	case 200, 301, 302, 307, 403:
		return true
	}
	return false
}

func (e *Engine) calibrate(target string) (BaselineResponse, error) {
	probe := joinURL(target, "wlrecon_probe_xzqq_invalid_9f3k")
	status, length, body, err := e.client.GetWithBody(probe)
	if err != nil {
		return BaselineResponse{}, err
	}
	return BaselineResponse{Status: status, Length: length, Body: body}, nil
}

func (e *Engine) isHit(status int, length int64, body string) bool {
	ms := e.cfg.MatchString
	is := e.cfg.InvalidString

	if ms != "" {
		return strings.Contains(body, ms)
	}
	if is != "" {
		return !strings.Contains(body, is)
	}
	return e.differsFromBaseline(status, length)
}

func (e *Engine) differsFromBaseline(status int, length int64) bool {
	if status != e.baseline.Status {
		return true
	}
	if e.baseline.Length >= 0 {
		diff := length - e.baseline.Length
		if diff < 0 {
			diff = -diff
		}
		return diff > 50
	}
	return false
}

func (e *Engine) processAt(target, word string, depth int) Result {
	word = strings.TrimSpace(word)
	if word == "" || strings.HasPrefix(word, "#") {
		return Result{Type: e.cfg.Mode, Result: word, Found: false}
	}

	var r Result
	switch e.cfg.Mode {
	case "dir":
		r = e.probeDirAt(target, word)
	case "endpoint":
		r = e.probeEndpointAt(target, word)
	case "user":
		r = e.probeUser(word)
	case "email":
		r = e.probeEmail(word)
	default:
		r = Result{Type: e.cfg.Mode, Error: "unknown mode: " + e.cfg.Mode}
	}
	r.Depth = depth
	return r
}

func (e *Engine) process(word string) Result {
	return e.processAt(e.cfg.Target, word, 0)
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
