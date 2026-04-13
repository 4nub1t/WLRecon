package main

import (
	"fmt"
	"net/url"
	"strings"
)

// --- dir ---

func (e *Engine) probeDirAtWithBaseline(target, word string, baseline BaselineResponse) Result {
	fullURL := joinURL(target, word)
	status, length, body, err := e.client.GetWithBody(fullURL)
	if err != nil {
		return Result{Type: "dir", Result: "/" + word, Found: false}
	}
	// Ruta completa desde el root original — funciona a cualquier profundidad
	path := strings.TrimPrefix(fullURL, strings.TrimRight(e.cfg.Target, "/"))
	if path == "" || path[0] != '/' {
		path = "/" + path
	}
	found := e.isHitWithBaseline(status, length, body, baseline)
	return Result{
		Type:   "dir",
		Result: path,
		Status: status,
		Length: length,
		Found:  found,
	}
}

// --- endpoint ---

func (e *Engine) probeEndpointAtWithBaseline(target, word string, baseline BaselineResponse) Result {
	candidate := word
	if !strings.HasPrefix(word, "/") {
		candidate = "/api/" + word
	}
	fullURL := strings.TrimRight(target, "/") + candidate
	status, length, body, err := e.client.GetWithBody(fullURL)
	if err != nil {
		return Result{Type: "endpoint", Result: candidate, Found: false}
	}
	// Ruta completa desde el root original
	path := strings.TrimPrefix(fullURL, strings.TrimRight(e.cfg.Target, "/"))
	if path == "" || path[0] != '/' {
		path = "/" + path
	}
	found := e.isHitWithBaseline(status, length, body, baseline)
	return Result{
		Type:   "endpoint",
		Result: path,
		Status: status,
		Length: length,
		Found:  found,
	}
}

// --- user ---

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

// --- email ---

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

// --- helpers ---

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
