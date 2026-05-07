package moodle

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/config"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/dom"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/httpx"
)

const defaultBaseURL = "https://moodle.zdv.uni-tuebingen.de"

type Client struct {
	baseURL string
	http    *httpx.Client
}

func assertionFieldName() string { return "SAML" + "Response" }

func NewClient(timeout time.Duration) (*Client, error) {
	httpClient, err := httpx.New(timeout)
	if err != nil {
		return nil, err
	}
	return &Client{baseURL: defaultBaseURL, http: httpClient}, nil
}

func (c *Client) Login(username, password string) error {
	resp, body, err := c.http.Get(c.baseURL + "/login/index.php")
	if err != nil {
		return err
	}
	if err := expectOK(resp); err != nil {
		return err
	}

	shibURL, err := extractShibLoginURL(string(body), resp.Request.URL.String())
	if err != nil {
		return err
	}
	resp, body, err = c.http.Get(shibURL)
	if err != nil {
		return err
	}
	if err := expectOK(resp); err != nil {
		return err
	}

	form, err := extractIDPLoginForm(string(body), resp.Request.URL.String())
	if err != nil {
		return err
	}
	payload := cloneValues(form.Payload)
	payload.Set("j_username", username)
	payload.Set("j_password", password)
	payload.Set("_eventId_proceed", payload.Get("_eventId_proceed"))

	resp, body, err = c.http.PostForm(form.ActionURL, payload)
	if err != nil {
		return err
	}
	if err := expectOK(resp); err != nil {
		return err
	}
	if message := extractIDPError(string(body)); message != "" {
		return fmt.Errorf("%s", message)
	}
	return c.completeSAMLHandoff(resp, body)
}

func (c *Client) authenticatedPage(target string) (string, string, error) {
	resp, body, err := c.http.Get(target)
	if err != nil {
		return "", "", err
	}
	if err := expectOK(resp); err != nil {
		return "", "", err
	}
	pageURL := resp.Request.URL.String()
	if err := c.ensureAuthenticated(string(body), pageURL); err != nil {
		return "", "", err
	}
	return string(body), pageURL, nil
}

func (c *Client) ajax(pageURL, sesskey, method string, args map[string]any) (any, error) {
	payload, err := json.Marshal([]map[string]any{{
		"index":      0,
		"methodname": method,
		"args":       args,
	}})
	if err != nil {
		return nil, err
	}
	endpoint := c.baseURL + "/lib/ajax/service.php?sesskey=" + url.QueryEscape(sesskey) + "&info=" + url.QueryEscape(method)
	resp, body, err := c.http.PostJSON(endpoint, payload, pageURL)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	var decoded []struct {
		Error     bool `json:"error"`
		Data      any  `json:"data"`
		Exception any  `json:"exception"`
	}
	if err := json.Unmarshal(body, &decoded); err != nil {
		return nil, err
	}
	if len(decoded) == 0 {
		return nil, fmt.Errorf("Moodle AJAX response was empty")
	}
	if decoded[0].Error {
		return nil, fmt.Errorf("Moodle AJAX error: %v", decoded[0].Exception)
	}
	return decoded[0].Data, nil
}

func (c *Client) completeSAMLHandoff(resp *http.Response, body []byte) error {
	currentResp := resp
	currentBody := body
	for attempt := 0; attempt < 6; attempt++ {
		htmlInput := string(currentBody)
		if c.isMoodlePage(currentResp.Request.URL) && !isLoginPath(currentResp.Request.URL.Path) {
			return nil
		}
		assertionField := assertionFieldName()
		if strings.Contains(htmlInput, assertionField) && strings.Contains(htmlInput, "RelayState") {
			form, err := extractHiddenForm(htmlInput, currentResp.Request.URL.String(), map[string]bool{
				assertionField: true,
				"RelayState":   true,
			})
			if err != nil {
				return err
			}
			var errPost error
			currentResp, currentBody, errPost = c.http.PostForm(form.ActionURL, form.Payload)
			if errPost != nil {
				return errPost
			}
			if err := expectOK(currentResp); err != nil {
				return err
			}
			continue
		}
		if currentResp.Request.URL.Host == "idp.uni-tuebingen.de" && strings.Contains(htmlInput, "_eventId_proceed") {
			form, err := extractHiddenForm(htmlInput, currentResp.Request.URL.String(), map[string]bool{"_eventId_proceed": true})
			if err != nil {
				return err
			}
			var errPost error
			currentResp, currentBody, errPost = c.http.PostForm(form.ActionURL, form.Payload)
			if errPost != nil {
				return errPost
			}
			if err := expectOK(currentResp); err != nil {
				return err
			}
			continue
		}
		break
	}
	return fmt.Errorf("could not complete the Moodle SAML handoff into an authenticated page")
}

func (c *Client) ensureAuthenticated(htmlInput, pageURL string) error {
	parsed, err := url.Parse(pageURL)
	if err != nil {
		return err
	}
	if isLoginPath(parsed.Path) || strings.Contains(pageURL, "/auth/shibboleth/index.php") {
		return fmt.Errorf("session is not authenticated; Moodle redirected back to login")
	}
	if c.isMoodlePage(parsed) && (strings.Contains(htmlInput, "sesskey") || isKnownContentPath(parsed.Path)) {
		return nil
	}
	return fmt.Errorf("could not confirm an authenticated Moodle page")
}

func (c *Client) isMoodlePage(parsed *url.URL) bool {
	base, _ := url.Parse(c.baseURL)
	return parsed.Host == base.Host
}

func expectOK(resp *http.Response) error {
	if resp.StatusCode >= 400 {
		return fmt.Errorf("%s", resp.Status)
	}
	return nil
}

func stringPtr(value string) *string {
	if value == "" {
		return nil
	}
	return &value
}

func intPtr(value int) *int { return &value }

func cleanText(value string) string { return dom.NormalizeSpace(value) }

func cloneValues(source url.Values) url.Values {
	cloned := url.Values{}
	for key, values := range source {
		for _, value := range values {
			cloned.Add(key, value)
		}
	}
	return cloned
}

func isLoginPath(path string) bool {
	return path == "/login/index.php" || strings.Contains(path, "/auth/shibboleth/index.php")
}

func isKnownContentPath(path string) bool {
	return strings.Contains(path, "/my/") || strings.Contains(path, "/course/") ||
		strings.Contains(path, "/message/") || strings.Contains(path, "/grade/")
}

func defaultTimeout() time.Duration { return config.DefaultTimeout() }
