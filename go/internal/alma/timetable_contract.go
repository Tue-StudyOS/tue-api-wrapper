package alma

import (
	"fmt"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/dom"
	"golang.org/x/net/html"
)

type timetableOption struct {
	Value      string
	Label      string
	IsSelected bool
}

type timetableContract struct {
	PageURL           string
	Terms             []timetableOption
	SelectedTermValue string
	SelectedTermLabel string
	ExportURL         string
}

func parseTimetableContract(htmlInput, pageURL string) (*timetableContract, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	scope := findTimetableForm(root)
	if scope == nil {
		scope = root
	}

	terms := parseSelectOptions(scope, "plan:scheduleConfiguration:anzeigeoptionen:changeTerm_input")
	selected := selectedOption(terms)

	exportURL := extractTextareaValue(scope, "plan:scheduleConfiguration:anzeigeoptionen:ical:cal_add")
	if len(terms) == 0 && exportURL == "" {
		return nil, fmt.Errorf("the response did not look like an Alma timetable page")
	}

	contract := &timetableContract{
		PageURL:   pageURL,
		Terms:     terms,
		ExportURL: exportURL,
	}
	if selected != nil {
		contract.SelectedTermValue = selected.Value
		contract.SelectedTermLabel = selected.Label
	}
	return contract, nil
}

func findTimetableForm(root *html.Node) *html.Node {
	form := dom.FindFirst(root, func(node *html.Node) bool {
		if !dom.IsElement(node, "form") {
			return false
		}
		id, ok := dom.Attr(node, "id")
		return ok && id == "plan"
	})
	if form != nil {
		return form
	}

	return dom.FindFirst(root, func(node *html.Node) bool {
		if !dom.IsElement(node, "form") {
			return false
		}
		action, _ := dom.Attr(node, "action")
		if strings.Contains(action, "individualTimetable") {
			return true
		}
		return findNamed(node, "select", "plan:scheduleConfiguration:anzeigeoptionen:changeTerm_input") != nil
	})
}

func parseSelectOptions(scope *html.Node, expectedName string) []timetableOption {
	selectNode := findNamed(scope, "select", expectedName)
	if selectNode == nil {
		return nil
	}

	var options []timetableOption
	for _, option := range dom.FindAll(selectNode, func(node *html.Node) bool { return dom.IsElement(node, "option") }) {
		value, _ := dom.Attr(option, "value")
		value = strings.TrimSpace(value)
		if value == "" {
			continue
		}
		label, _ := dom.Attr(option, "data-title")
		label = strings.TrimSpace(label)
		if label == "" {
			label = dom.Text(option)
		}
		label = strings.TrimSpace(label)
		if label == "" {
			continue
		}
		options = append(options, timetableOption{
			Value:      value,
			Label:      label,
			IsSelected: hasAttribute(option, "selected"),
		})
	}
	return options
}

func selectedOption(options []timetableOption) *timetableOption {
	for i := range options {
		if options[i].IsSelected {
			return &options[i]
		}
	}
	return nil
}

func extractTextareaValue(scope *html.Node, expectedName string) string {
	node := findNamed(scope, "textarea", expectedName)
	if node == nil {
		return ""
	}
	value := strings.TrimSpace(rawNodeText(node))
	return value
}

func rawNodeText(node *html.Node) string {
	var parts []string
	var walk func(*html.Node)
	walk = func(current *html.Node) {
		if current == nil {
			return
		}
		if current.Type == html.TextNode {
			parts = append(parts, current.Data)
		}
		for child := current.FirstChild; child != nil; child = child.NextSibling {
			walk(child)
		}
	}
	walk(node)
	return strings.Join(parts, "")
}

func hasAttribute(node *html.Node, key string) bool {
	_, ok := dom.Attr(node, key)
	return ok
}

func findNamed(scope *html.Node, tag string, expectedName string) *html.Node {
	matches := buildFieldMatcher(expectedName)
	return dom.FindFirst(scope, func(node *html.Node) bool {
		if tag != "" && !(dom.IsElement(node, tag)) {
			return false
		}
		if name, ok := dom.Attr(node, "name"); ok && matches(name) {
			return true
		}
		if id, ok := dom.Attr(node, "id"); ok && matches(id) {
			return true
		}
		return false
	})
}

func buildFieldMatcher(expected string) func(string) bool {
	parts := strings.Split(expected, ":")
	suffixes := []string{":" + parts[len(parts)-1]}
	if len(parts) > 1 {
		suffixes = append([]string{":" + strings.Join(parts[1:], ":")}, suffixes...)
	}
	return func(value string) bool {
		value = strings.TrimSpace(value)
		if value == "" {
			return false
		}
		if value == expected {
			return true
		}
		for _, suffix := range suffixes {
			if strings.HasSuffix(value, suffix) {
				return true
			}
		}
		return false
	}
}
