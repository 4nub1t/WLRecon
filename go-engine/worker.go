package main

import (
	"fmt"
	"net/url"
	"strings"
)

// Directory bruteforce: GET /<word>
func (e *Engine) probeDir(word string) Result {
	target := joinURL(e.cfg.Target, word)
	status, err := e.client.Get(target)
	if err != nil {
		return Result{Type: "dir", Result: word, Found: false}
	}
	found := isHit(status)
	return Result{
		Type:   "dir",
		Result: "/" + word,
		Status: status,
		Found:  found,
	}
}

// Endpoint discovery: GET /api/<word> or custom path pattern
func (e *Engine) probeEndpoint(word string) Result {
	candidate := word
	if !strings.HasPrefix(word, "/") {
		candidate = "/api/" + word
	}
	target := strings.TrimRight(e.cfg.Target, "/") + candidate
	status, err := e.client.Get(target)
	if err != nil {
		return Result{Type: "endpoint", Result: candidate, Found: false}
	}
	found := isHit(status)
	return Result{
		Type:   "endpoint",
		Result: candidate,
		Status: status,
		Found:  found,
	}
}

// Username enumeration: POST to login endpoint, infer validity from response code
// Convention: target URL must be the login form endpoint (e.g. http://host/login)
// Valid user detection heuristic: non-404 response for the username probe
func (e *Engine) probeUser(word string) Result {
	body := fmt.Sprintf("username=%s&password=invalid_probe_wlrecon", url.QueryEscape(word))
	status, err := e.client.Post(e.cfg.Target, body, "application/x-www-form-urlencoded")
	if err != nil {
		return Result{Type: "user", Result: word, Found: false}
	}
	// Heuristic: 200 or 302 for a non-existent user is ambiguous;
	// a 200 with invalid creds on a real user vs non-existent user
	// often returns different status codes (e.g. 200 vs 404).
	// Operators should tune based on target behaviour.
	found := status != 404 && status != 400 && status != 0
	return Result{
		Type:   "user",
		Result: word,
		Status: status,
		Found:  found,
	}
}

// Email enumeration: POST to password reset or login endpoint
func (e *Engine) probeEmail(word string) Result {
	var email string
	if strings.Contains(word, "@") {
		email = word
	} else {
		email = word + "@" + extractDomain(e.cfg.Target)
	}
	body := fmt.Sprintf("email=%s", url.QueryEscape(email))
	status, err := e.client.Post(e.cfg.Target, body, "application/x-www-form-urlencoded")
	if err != nil {
		return Result{Type: "email", Result: email, Found: false}
	}
	found := status == 200 || status == 302
	return Result{
		Type:   "email",
		Result: email,
		Status: status,
		Found:  found,
	}
}

func isHit(status int) bool {
	switch status {
	case 200, 201, 204, 301, 302, 307, 308, 401, 403:
		return true
	}
	return false
}

func extractDomain(rawURL string) string {
	u, err := url.Parse(rawURL)
	if err != nil {
		return "target.local"
	}
	host := u.Hostname()
	if host == "" {
		return "target.local"
	}
	return host
}
