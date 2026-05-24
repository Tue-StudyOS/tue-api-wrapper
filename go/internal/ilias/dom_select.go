package ilias

import (
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/dom"
	"golang.org/x/net/html"
)

func firstDescendant(node *html.Node, tag string, className string) *html.Node {
	return dom.FindFirst(node, func(candidate *html.Node) bool {
		if !dom.IsElement(candidate, tag) {
			return false
		}
		return dom.HasClass(candidate, className) || hasClassAncestor(candidate, className)
	})
}

func firstImageAlt(node *html.Node) *string {
	image := dom.FindFirst(node, func(candidate *html.Node) bool {
		if !dom.IsElement(candidate, "img") {
			return false
		}
		_, ok := dom.Attr(candidate, "alt")
		return ok
	})
	if image == nil {
		return nil
	}
	value, _ := dom.Attr(image, "alt")
	return stringPtrOrNil(value)
}

func classTextPtr(node *html.Node, className string) *string {
	return firstClassTextPtr(node, className)
}

func firstClassTextPtr(node *html.Node, className string) *string {
	found := dom.FindFirst(node, func(candidate *html.Node) bool {
		return dom.HasClass(candidate, className)
	})
	if found == nil {
		return nil
	}
	return stringPtrOrNil(dom.Text(found))
}

func classTexts(node *html.Node, className string) []string {
	var values []string
	for _, found := range dom.FindAll(node, func(candidate *html.Node) bool {
		return dom.HasClass(candidate, className)
	}) {
		text := dom.Text(found)
		if text != "" {
			values = append(values, text)
		}
	}
	return values
}

func itemProperties(node *html.Node) map[string]string {
	properties := map[string]string{}
	for _, nameNode := range dom.FindAll(node, func(candidate *html.Node) bool {
		return dom.HasClass(candidate, "il-item-property-name")
	}) {
		valueNode := nextElementSiblingWithClass(nameNode, "il-item-property-value")
		name := strings.TrimSuffix(dom.Text(nameNode), ":")
		if name != "" && valueNode != nil {
			properties[name] = dom.Text(valueNode)
		}
	}
	return properties
}

func propertyLines(node *html.Node) []string {
	properties := itemProperties(node)
	var lines []string
	for key, value := range properties {
		if value == "" {
			continue
		}
		if key == "" {
			lines = append(lines, value)
		} else {
			lines = append(lines, key+": "+value)
		}
	}
	return lines
}

func nextElementSiblingWithClass(node *html.Node, className string) *html.Node {
	for sibling := node.NextSibling; sibling != nil; sibling = sibling.NextSibling {
		if sibling.Type == html.ElementNode && dom.HasClass(sibling, className) {
			return sibling
		}
	}
	return nil
}

func firstButtonAction(node *html.Node) *string {
	button := dom.FindFirst(node, func(candidate *html.Node) bool {
		if !dom.IsElement(candidate, "button") {
			return false
		}
		value, ok := dom.Attr(candidate, "data-action")
		return ok && value != ""
	})
	if button == nil {
		return nil
	}
	value, _ := dom.Attr(button, "data-action")
	return stringPtr(resolveURL(iliasBaseURL, value))
}

func hrefOrAction(node *html.Node, pageURL string) string {
	if href, ok := dom.Attr(node, "href"); ok && href != "" {
		return resolveURL(pageURL, href)
	}
	if action, ok := dom.Attr(node, "data-action"); ok && action != "" {
		return resolveURL(pageURL, action)
	}
	return ""
}

func mustHref(node *html.Node, pageURL string) string {
	if href, ok := dom.Attr(node, "href"); ok && href != "" {
		return resolveURL(pageURL, href)
	}
	return pageURL
}

func firstMapValue(values map[string]string, keys ...string) *string {
	for _, key := range keys {
		if value := strings.TrimSpace(values[key]); value != "" {
			return stringPtr(value)
		}
	}
	return nil
}

func stringPtrOrNil(value string) *string {
	value = dom.NormalizeSpace(value)
	if value == "" {
		return nil
	}
	return stringPtr(value)
}
