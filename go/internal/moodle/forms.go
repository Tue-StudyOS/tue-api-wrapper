package moodle

import (
	"fmt"
	"net/url"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/dom"
	"golang.org/x/net/html"
)

type loginForm struct {
	ActionURL string
	Payload   url.Values
}

func extractShibLoginURL(htmlInput, pageURL string) (string, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return "", err
	}
	link := dom.FindFirst(root, func(node *html.Node) bool {
		if !dom.IsElement(node, "a") {
			return false
		}
		href, ok := dom.Attr(node, "href")
		return ok && strings.Contains(href, "/auth/shibboleth/index.php")
	})
	if link == nil {
		return "", fmt.Errorf("could not find the Moodle Shibboleth login link")
	}
	href, _ := dom.Attr(link, "href")
	return resolveURL(pageURL, href), nil
}

func extractIDPLoginForm(htmlInput, pageURL string) (*loginForm, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	formNode := dom.FindFirst(root, func(node *html.Node) bool {
		if !dom.IsElement(node, "form") {
			return false
		}
		password := dom.FindFirst(node, func(node *html.Node) bool {
			if !dom.IsElement(node, "input") {
				return false
			}
			name, _ := dom.Attr(node, "name")
			return name == "j_password"
		})
		return password != nil
	})
	if formNode == nil {
		return nil, fmt.Errorf("could not find the Shibboleth IdP username/password form")
	}
	return formPayload(formNode, pageURL, nil)
}

func extractHiddenForm(htmlInput, pageURL string, required map[string]bool) (*loginForm, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	for _, formNode := range dom.FindAll(root, func(node *html.Node) bool { return dom.IsElement(node, "form") }) {
		form, err := formPayload(formNode, pageURL, required)
		if err == nil {
			return form, nil
		}
	}
	return nil, fmt.Errorf("could not find a form with the required hidden fields")
}

func formPayload(formNode *html.Node, pageURL string, required map[string]bool) (*loginForm, error) {
	action, _ := dom.Attr(formNode, "action")
	payload := url.Values{}
	for _, input := range dom.FindAll(formNode, func(node *html.Node) bool { return dom.IsElement(node, "input") }) {
		name, ok := dom.Attr(input, "name")
		if !ok || name == "" {
			continue
		}
		fieldType, _ := dom.Attr(input, "type")
		if fieldType == "checkbox" {
			continue
		}
		value, _ := dom.Attr(input, "value")
		payload.Set(name, value)
	}
	if required != nil && !hasAllRequired(payload, required) {
		return nil, fmt.Errorf("form missing required fields")
	}
	return &loginForm{ActionURL: resolveURL(pageURL, action), Payload: payload}, nil
}

func hasAllRequired(payload url.Values, required map[string]bool) bool {
	for key := range required {
		if _, ok := payload[key]; !ok {
			return false
		}
	}
	return true
}

func extractIDPError(htmlInput string) string {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return ""
	}
	node := dom.FindFirst(root, func(node *html.Node) bool {
		return dom.IsElement(node, "div") && dom.HasClass(node, "form-error")
	})
	if node == nil {
		return ""
	}
	return dom.Text(node)
}

func resolveURL(baseURL, relative string) string {
	base, err := url.Parse(baseURL)
	if err != nil {
		return relative
	}
	target, err := url.Parse(relative)
	if err != nil {
		return relative
	}
	return base.ResolveReference(target).String()
}
