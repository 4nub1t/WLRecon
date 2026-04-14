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
	Mode               string
	Target             string
	Wordlist           string
	Threads            int
	Timeout            int
	Proxy              string
	MatchString        string
	InvalidString      string
	ExtraHeaders       string
	ExtraParams        string
	TLSSkip            bool
	Recursive          bool
	MaxDepth           int
	MaxRecursePerLevel int
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
	cfg          EngineConfig
	client       *HTTPClient
	output       chan interface{}
	initBaseline BaselineResponse
	visited      map[string]bool
	mu           sync.Mutex
	wg           sync.WaitGroup
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
		baseline = BaselineResponse{Status: 404, Length: -1}
	}
	e.initBaseline = baseline

	start := time.Now()

	e.wg.Add(1)
	go e.emitOutputs()

	total, found := e.scanTarget(e.cfg.Target, words, 0, baseline)

	e.output <- SummaryResult{
		Type:       "summary",
		Total:      total,
		FoundCount: found,
		ElapsedMs:  time.Since(start).Milliseconds(),
	}

	close(e.output)
	e.wg.Wait()

	return nil
}

func (e *Engine) emitOutputs() {
	defer e.wg.Done()

	enc := json.NewEncoder(os.Stdout)

	for item := range e.output {
		_ = enc.Encode(item)
		_ = os.Stdout.Sync()
	}
}

func (e *Engine) scanTarget(target string, words []string, depth int, baseline BaselineResponse) (int, int64) {
	e.mu.Lock()
	if e.visited[target] {
		e.mu.Unlock()
		return 0, 0
	}
	e.visited[target] = true
	e.mu.Unlock()

	if depth > 0 && isBaselineMode(e.cfg.Mode) {
		if b, err := e.calibrate(target); err == nil {
			baseline = b
		}
	}

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

				result := e.process(target, word, depth, baseline)

				counter.Add(1)

				if result.Found {
					found.Add(1)

					if e.cfg.Recursive && depth < e.cfg.MaxDepth {
						if isRecursable(result.Status) {
							newTarget := strings.TrimRight(target, "/") + result.Result

							recurseMu.Lock()
							if e.cfg.MaxRecursePerLevel == 0 || len(recurseTargets) < e.cfg.MaxRecursePerLevel {
								recurseTargets = append(recurseTargets, newTarget)
							}
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

	for _, sub := range recurseTargets {
		subTotal, subFound := e.scanTarget(sub, words, depth+1, baseline)
		total += subTotal
		found.Add(subFound)
	}

	return total, found.Load()
}


func (e *Engine) process(target, word string, depth int, baseline BaselineResponse) Result {
	word = strings.TrimSpace(word)
	if word == "" || strings.HasPrefix(word, "#") {
		return Result{Type: e.cfg.Mode, Result: word, Found: false}
	}

	var r Result

	switch e.cfg.Mode {

	case "dir":
		r = e.probeDirAtWithBaseline(target, word, baseline)

	case "endpoint":
		r = e.probeEndpointAtWithBaseline(target, word, baseline)

	case "user":
		r = e.probeUser(word)

	case "email":
		r = e.probeEmail(word)

	default:
		r = Result{Type: e.cfg.Mode, Error: "unknown mode"}
	}

	r.Depth = depth
	return r
}


func (e *Engine) isHit(status int, length int64, body string) bool {

	// AUTH MODES → NO baseline logic
	if e.cfg.Mode == "user" || e.cfg.Mode == "email" {

		if e.cfg.InvalidString != "" {
			return !strings.Contains(body, e.cfg.InvalidString)
		}

		if e.cfg.MatchString != "" {
			return strings.Contains(body, e.cfg.MatchString)
		}

		// safer fallback (avoid 100% false positives)
		return status >= 200 && status < 300 && length > 0
	}

	return e.isHitWithBaseline(status, length, body, e.initBaseline)
}

func (e *Engine) isHitWithBaseline(status int, length int64, body string, baseline BaselineResponse) bool {

	if e.cfg.MatchString != "" {
		return strings.Contains(body, e.cfg.MatchString)
	}

	if e.cfg.InvalidString != "" {
		return !strings.Contains(body, e.cfg.InvalidString)
	}

	if status != baseline.Status {
		return true
	}

	if baseline.Length >= 0 {
		diff := length - baseline.Length
		if diff < 0 {
			diff = -diff
		}
		return diff > 50
	}

	return false
}


func isBaselineMode(mode string) bool {
	return mode == "dir" || mode == "endpoint"
}

func isRecursable(status int) bool {
	return status == 200 || status == 301 || status == 302 || status == 307
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
