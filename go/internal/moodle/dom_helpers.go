package moodle

import (
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/dom"
	"golang.org/x/net/html"
)

func findLink(node *html.Node, contains []string) *html.Node {
	return dom.FindFirst(node, func(candidate *html.Node) bool {
		if !dom.IsElement(candidate, "a") {
			return false
		}
		href, ok := dom.Attr(candidate, "href")
		if !ok {
			return false
		}
		for _, token := range contains {
			if token == "" || strings.Contains(href, token) {
				return true
			}
		}
		return false
	})
}

func linksContaining(node *html.Node, token string) []*html.Node {
	return dom.FindAll(node, func(candidate *html.Node) bool {
		if !dom.IsElement(candidate, "a") {
			return false
		}
		href, ok := dom.Attr(candidate, "href")
		return ok && strings.Contains(href, token)
	})
}

func firstText(root *html.Node, tags []string) string {
	for _, tag := range tags {
		node := dom.FindFirst(root, func(candidate *html.Node) bool { return dom.IsElement(candidate, tag) })
		if node != nil {
			if text := cleanText(dom.Text(node)); text != "" {
				return text
			}
		}
	}
	return ""
}

func texts(nodes []*html.Node) []string {
	seen := map[string]bool{}
	values := []string{}
	for _, node := range nodes {
		text := cleanText(dom.Text(node))
		if text != "" && !seen[text] {
			values = append(values, text)
			seen[text] = true
		}
	}
	return values
}

func firstListItems(root *html.Node, selectors []string) []*html.Node {
	for _, selector := range selectors {
		nodes := nodesForSimpleSelector(root, selector)
		if len(nodes) > 0 {
			return nodes
		}
	}
	return nil
}

func nodesForSimpleSelector(root *html.Node, selector string) []*html.Node {
	if strings.HasPrefix(selector, ".") {
		return nodesWithClass(root, strings.TrimPrefix(selector, "."))
	}
	if selector == "li" {
		return dom.FindAll(root, func(node *html.Node) bool { return dom.IsElement(node, "li") })
	}
	if selector == "table.generaltable tbody tr" {
		return dom.FindAll(root, func(node *html.Node) bool { return dom.IsElement(node, "tr") })
	}
	return nil
}

func nodesWithClass(root *html.Node, className string) []*html.Node {
	return dom.FindAll(root, func(node *html.Node) bool { return classContains(node, className) })
}

func firstNodeWithClass(root *html.Node, className string) *html.Node {
	return dom.FindFirst(root, func(node *html.Node) bool { return classContains(node, className) })
}

func classContains(node *html.Node, token string) bool {
	value, ok := dom.Attr(node, "class")
	if !ok {
		return false
	}
	for _, className := range strings.Fields(value) {
		if className == token || strings.Contains(className, token) {
			return true
		}
	}
	return false
}

func pageTitle(root *html.Node) string {
	for _, tag := range []string{"h1", "title"} {
		node := dom.FindFirst(root, func(candidate *html.Node) bool { return dom.IsElement(candidate, tag) })
		if node != nil {
			if text := cleanText(dom.Text(node)); text != "" {
				return text
			}
		}
	}
	return "Moodle"
}

func courseSummary(box *html.Node, pageURL string) map[string]any {
	link := findLink(box, []string{"/course/view.php?id="})
	if link == nil {
		return nil
	}
	href, _ := dom.Attr(link, "href")
	fullURL := resolveURL(pageURL, href)
	title := cleanText(dom.Text(link))
	if title == "" {
		return nil
	}
	item := map[string]any{"title": title, "url": fullURL}
	if id := queryInt(fullURL, "id"); id != nil {
		item["id"] = *id
	}
	if summary := firstText(box, []string{"div"}); summary != "" && summary != title {
		item["summary"] = summary
	}
	teachers := texts(linksContaining(box, "/user/"))
	if len(teachers) > 0 {
		item["teachers"] = teachers
	}
	return item
}

func enrolmentForm(root *html.Node, pageURL string) *loginForm {
	for _, formNode := range dom.FindAll(root, func(node *html.Node) bool { return dom.IsElement(node, "form") }) {
		action, _ := dom.Attr(formNode, "action")
		if strings.Contains(resolveURL(pageURL, action), "/enrol/index.php") {
			form, err := formPayload(formNode, pageURL, nil)
			if err == nil {
				return form
			}
		}
	}
	return nil
}

func passwordFieldName(root *html.Node) string {
	node := dom.FindFirst(root, func(candidate *html.Node) bool {
		if !dom.IsElement(candidate, "input") {
			return false
		}
		fieldType, _ := dom.Attr(candidate, "type")
		_, hasName := dom.Attr(candidate, "name")
		return fieldType == "password" && hasName
	})
	if node == nil {
		return ""
	}
	name, _ := dom.Attr(node, "name")
	return name
}

func extractPageMessage(htmlInput string) *string {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil
	}
	for _, className := range []string{"alert-danger", "alert-warning", "notifyproblem", "errorbox", "loginerrors"} {
		node := firstNodeWithClass(root, className)
		if node == nil {
			continue
		}
		if text := cleanText(dom.Text(node)); text != "" {
			return stringPtr(text)
		}
	}
	return nil
}
