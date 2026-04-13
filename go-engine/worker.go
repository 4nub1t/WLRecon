package main

import (
	"fmt"
	"net/url"
	"strings"
)

func (e *Engine) probeDirAt(target, word string) Result {
	fullURL := joinURL(target, word)
	status, length, body, err := e.client.GetWithBody(fullURL)
	if err != nil {
		return Result{Type: "dir", Result: "/" + word, Found: false}
	}
	found := e.isHit(status, length, body)
	return Result{
		Type:   "dir",
		Result: "/" + word,
		Status: status,
		Length: length,
		Found:  found,
	}
}

func (e *Engine) probeEndpointAt(target, word string) Result {
	candidate := word
	if !strings.HasPrefix(word, "/") {
		candidate = "/api/" + word
	}
	fullURL := strings.TrimRight(target, "/") + candidate
	status, length, body, err := e.client.GetWithBody(fullURL)
	if err != nil {
		return Result{Type: "endpoint", Result: candidate, Found: false}
	}
	found := e.isHit(status, length, body)
	return Result{
		Type:   "endpoint",
		Result: candidate,
		Status: status,
		Length: length,
		Found:  found,
	}
}

// Keep old methods as wrappers for compatibility
func (e *Engine) probeDir(word string) Result {
	return e.probeDirAt(e.cfg.Target, word)
}

func (e *Engine) probeEndpoint(word string) Result {
	return e.probeEndpointAt(e.cfg.Target, word)
}

func (e *Engine) probeUser(word string) Result {
	body := fmt.Sprintf("username=%s&password=invalid_probe_wlrecon", url.QueryEscape(word))
	if e.cfg.ExtraParams != "" {
		body += "&" + e.cfg.ExtraParams
	}
	status, length, respBody, err := e.client.PostWithBody(e.cfg.Target, body, "application/x-www-form-urlencoded")
	if err != nil {
		return Result{Type: "user", Result: word, Found: false}
	}
	found := e.isHit(status, length, respBody)
	return Result{
		Type:   "user",
		Result: word,
		Status: status,
		Length: length,
		Found:  found,
	}
}

func (e *Engine) probeEmail(word string) Result {
	var email string
	if strings.Contains(word, "@") {
		email = word
	} else {
		email = word + "@" + extractDomain(e.cfg.Target)
	}
	body := fmt.Sprintf("username=%s&password=invalid_probe_wlrecon", url.QueryEscape(email))
	if e.cfg.ExtraParams != "" {
		body += "&" + e.cfg.ExtraParams
	}
	status, length, respBody, err := e.client.PostWithBody(e.cfg.Target, body, "application/x-www-form-urlencoded")
	if err != nil {
		return Result{Type: "email", Result: email, Found: false}
	}
	found := e.isHit(status, length, respBody)
	return Result{
		Type:   "email",
		Result: email,
		Status: status,
		Length: length,
		Found:  found,
	}
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
