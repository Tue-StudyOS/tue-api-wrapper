package moodle

import (
	"encoding/json"
	"fmt"
	"net/url"
	"regexp"
	"strconv"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/dom"
	"golang.org/x/net/html"
)

var moodleConfigPattern = regexp.MustCompile(`M\.cfg\s*=\s*(\{.*?\});`)

type pageConfig struct {
	Sesskey string `json:"sesskey"`
}

func extractPageConfig(htmlInput string) (*pageConfig, error) {
	matches := moodleConfigPattern.FindStringSubmatch(htmlInput)
	if len(matches) < 2 {
		return nil, fmt.Errorf("could not find the Moodle page config payload")
	}
	var cfg pageConfig
	if err := json.Unmarshal([]byte(matches[1]), &cfg); err != nil {
		return nil, err
	}
	if strings.TrimSpace(cfg.Sesskey) == "" {
		return nil, fmt.Errorf("could not find a Moodle sesskey in the page config")
	}
	return &cfg, nil
}

func parseGradesPage(htmlInput, pageURL string, limit int) (*GradesPage, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	items := []GradeItem{}
	for _, row := range firstMatchingTableRows(root, []string{"grade", "bewertung", "course", "kurs"}) {
		cells := rowCells(row)
		values := []string{}
		for _, cell := range cells {
			if text := cleanText(dom.Text(cell)); text != "" {
				values = append(values, text)
			}
		}
		if len(values) == 0 {
			continue
		}
		link := findLink(row, []string{"/course/view.php", "/grade/"})
		courseTitle := values[0]
		var itemURL *string
		if link != nil {
			courseTitle = cleanText(dom.Text(link))
			if href, ok := dom.Attr(link, "href"); ok {
				itemURL = stringPtr(resolveURL(pageURL, href))
			}
		}
		tail := withoutValue(values, courseTitle)
		items = append(items, GradeItem{
			CourseTitle: courseTitle,
			Grade:       tailPtr(tail, 0),
			Percentage:  tailPtr(tail, 1),
			RangeHint:   tailPtr(tail, 2),
			Rank:        tailPtr(tail, 3),
			Feedback:    tailPtr(tail, 4),
			URL:         itemURL,
		})
		if limit > 0 && len(items) >= limit {
			break
		}
	}
	return &GradesPage{SourceURL: pageURL, Items: items}, nil
}

func parseFeedPage(htmlInput, pageURL string, selectors []string) (*FeedPage, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	nodes := firstListItems(root, selectors)
	items := []FeedItem{}
	for _, node := range nodes {
		text := cleanText(dom.Text(node))
		if text == "" {
			continue
		}
		link := findLink(node, []string{""})
		title := firstText(node, []string{"strong", "a"})
		if title == "" {
			title = text
		}
		var itemURL *string
		if link != nil {
			if href, ok := dom.Attr(link, "href"); ok {
				itemURL = stringPtr(resolveURL(pageURL, href))
			}
		}
		items = append(items, FeedItem{
			Title:  title,
			Body:   stringPtr(text),
			URL:    itemURL,
			Unread: boolPtr(classContains(node, "unread")),
		})
	}
	return &FeedPage{SourceURL: pageURL, Items: items}, nil
}

func parseCategoryPage(htmlInput, pageURL string) (*CategoryPage, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	page := &CategoryPage{SourceURL: pageURL, Title: pageTitle(root)}
	seenCategories := map[int]bool{}
	for _, link := range linksContaining(root, "/course/index.php?categoryid=") {
		href, _ := dom.Attr(link, "href")
		fullURL := resolveURL(pageURL, href)
		id := queryInt(fullURL, "categoryid")
		if id != nil && seenCategories[*id] {
			continue
		}
		if id != nil {
			seenCategories[*id] = true
		}
		title := cleanText(dom.Text(link))
		if title == "" {
			continue
		}
		page.Categories = append(page.Categories, CategoryItem{ID: id, Title: title, URL: stringPtr(fullURL)})
	}
	for _, box := range nodesWithClass(root, "coursebox") {
		if course := courseSummary(box, pageURL); course != nil {
			page.Courses = append(page.Courses, course)
		}
	}
	return page, nil
}

func parseCourseDetail(htmlInput, pageURL string) (*CourseDetail, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	box := firstNodeWithClass(root, "coursebox")
	if box == nil {
		box = root
	}
	title := firstText(box, []string{"h1", "h2", "h3", "a"})
	if title == "" {
		title = pageTitle(root)
	}
	detail := &CourseDetail{SourceURL: pageURL, Title: title, EnrolmentPayload: map[string]string{}}
	if link := findLink(box, []string{"/course/view.php?id="}); link != nil {
		href, _ := dom.Attr(link, "href")
		fullURL := resolveURL(pageURL, href)
		detail.CourseURL = stringPtr(fullURL)
		detail.ID = queryInt(fullURL, "id")
	}
	detail.Summary = stringPtr(firstText(box, []string{"div"}))
	detail.Teachers = texts(linksContaining(box, "/user/"))
	if form := enrolmentForm(root, pageURL); form != nil {
		detail.SelfEnrolmentAvailable = true
		detail.EnrolmentActionURL = stringPtr(form.ActionURL)
		for key, values := range form.Payload {
			if len(values) > 0 {
				detail.EnrolmentPayload[key] = values[0]
			}
		}
		detail.ID = firstIntPtr(detail.ID, queryInt(form.ActionURL, "id"), intFromString(detail.EnrolmentPayload["id"]))
		if name := passwordFieldName(root); name != "" {
			detail.EnrolmentKeyFieldName = stringPtr(name)
			detail.RequiresEnrolmentKey = !strings.Contains(htmlInput, "Kein Einschreibekennwort notwendig")
		}
		detail.NoEnrolmentKeyRequired = strings.Contains(htmlInput, "Kein Einschreibekennwort notwendig")
	}
	return detail, nil
}

func firstMatchingTableRows(root *html.Node, keywords []string) []*html.Node {
	for _, table := range dom.FindAll(root, func(node *html.Node) bool { return dom.IsElement(node, "table") }) {
		headers := []string{}
		for _, th := range dom.FindAll(table, func(node *html.Node) bool { return dom.IsElement(node, "th") }) {
			headers = append(headers, strings.ToLower(cleanText(dom.Text(th))))
		}
		if len(headers) > 0 && !containsAny(headers, keywords) {
			continue
		}
		rows := []*html.Node{}
		for _, row := range dom.FindAll(table, func(node *html.Node) bool { return dom.IsElement(node, "tr") }) {
			cells := rowCells(row)
			if len(cells) < 2 || hasElement(row, "th") {
				continue
			}
			rows = append(rows, row)
		}
		if len(rows) > 0 {
			return rows
		}
	}
	return nil
}

func rowCells(row *html.Node) []*html.Node {
	return dom.FindAll(row, func(node *html.Node) bool { return dom.IsElement(node, "td") || dom.IsElement(node, "th") })
}

func hasElement(node *html.Node, tag string) bool {
	return dom.FindFirst(node, func(node *html.Node) bool { return dom.IsElement(node, tag) }) != nil
}

func containsAny(values, keywords []string) bool {
	for _, value := range values {
		for _, keyword := range keywords {
			if strings.Contains(value, keyword) {
				return true
			}
		}
	}
	return false
}

func tailPtr(values []string, index int) *string {
	if index >= len(values) {
		return nil
	}
	return stringPtr(values[index])
}

func withoutValue(values []string, skip string) []string {
	result := []string{}
	for _, value := range values {
		if value != skip {
			result = append(result, value)
		}
	}
	return result
}

func boolPtr(value bool) *bool { return &value }

func intFromString(value string) *int {
	if value == "" {
		return nil
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		return nil
	}
	return intPtr(parsed)
}

func firstIntPtr(values ...*int) *int {
	for _, value := range values {
		if value != nil {
			return value
		}
	}
	return nil
}

func queryInt(rawURL, key string) *int {
	parsed, err := url.Parse(rawURL)
	if err != nil {
		return nil
	}
	return intFromString(parsed.Query().Get(key))
}
