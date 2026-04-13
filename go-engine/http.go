package main

import (
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type HTTPClient struct {
	client       *http.Client
	extraHeaders map[string]string
}

func NewHTTPClient(timeoutSec int, proxy string, extraHeaders string) *HTTPClient {
	transport := &http.Transport{
		MaxIdleConns:        200,
		MaxIdleConnsPerHost: 50,
		IdleConnTimeout:     30 * time.Second,
		DisableKeepAlives:   false,
	}

	if proxy != "" {
		proxyURL, err := url.Parse(proxy)
		if err == nil {
			transport.Proxy = http.ProxyURL(proxyURL)
		}
	}

	headers := parseHeaders(extraHeaders)

	return &HTTPClient{
		client: &http.Client{
			Transport: transport,
			Timeout:   time.Duration(timeoutSec) * time.Second,
			CheckRedirect: func(req *http.Request, via []*http.Request) error {
				if len(via) >= 3 {
					return http.ErrUseLastResponse
				}
				return nil
			},
		},
		extraHeaders: headers,
	}
}

func parseHeaders(raw string) map[string]string {
	headers := map[string]string{}
	if raw == "" {
		return headers
	}
	for _, pair := range strings.Split(raw, ",") {
		parts := strings.SplitN(strings.TrimSpace(pair), ":", 2)
		if len(parts) == 2 {
			headers[strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
		}
	}
	return headers
}

func (h *HTTPClient) applyHeaders(req *http.Request) {
	req.Header.Set("User-Agent", "WLRecon/1.0 (OSCP/RedTeam)")
	req.Header.Set("Accept", "*/*")
	req.Header.Set("Connection", "keep-alive")
	for k, v := range h.extraHeaders {
		req.Header.Set(k, v)
	}
}

func (h *HTTPClient) GetWithBody(rawURL string) (int, int64, string, error) {
	req, err := http.NewRequest(http.MethodGet, rawURL, nil)
	if err != nil {
		return 0, 0, "", err
	}
	h.applyHeaders(req)

	resp, err := h.client.Do(req)
	if err != nil {
		return 0, 0, "", err
	}
	defer resp.Body.Close()
	bodyBytes, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, int64(len(bodyBytes)), string(bodyBytes), nil
}

func (h *HTTPClient) PostWithBody(rawURL string, body string, contentType string) (int, int64, string, error) {
	req, err := http.NewRequest(http.MethodPost, rawURL, strings.NewReader(body))
	if err != nil {
		return 0, 0, "", err
	}
	h.applyHeaders(req)
	req.Header.Set("Content-Type", contentType)

	resp, err := h.client.Do(req)
	if err != nil {
		return 0, 0, "", err
	}
	defer resp.Body.Close()
	bodyBytes, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, int64(len(bodyBytes)), string(bodyBytes), nil
}

func joinURL(base, path string) string {
	base = strings.TrimRight(base, "/")
	path = strings.TrimLeft(path, "/")
	return fmt.Sprintf("%s/%s", base, path)
}
