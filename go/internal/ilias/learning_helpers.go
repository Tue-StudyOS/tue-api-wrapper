package ilias

import (
	"net/url"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/dom"
	"golang.org/x/net/html"
)

func parseForumTopics(htmlInput, pageURL string) ([]ForumTopic, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	var topics []ForumTopic
	for _, row := range standardItems(root) {
		titleLink := firstDescendant(row, "a", "il-item-title")
		if titleLink == nil {
			continue
		}
		props := itemProperties(row)
		topics = append(topics, ForumTopic{
			Title:    dom.Text(titleLink),
			URL:      mustHref(titleLink, pageURL),
			Author:   stringPtrOrNil(props["Angelegt von"]),
			Posts:    stringPtrOrNil(props["Beiträge"]),
			LastPost: stringPtrOrNil(props["Letzter Beitrag"]),
			Visits:   stringPtrOrNil(props["Besuche"]),
		})
	}
	if len(topics) == 0 && !isAuthenticatedPage(htmlInput, pageURL) {
		return nil, errNotAuthenticated("forum")
	}
	return topics, nil
}

func parseExerciseAssignments(htmlInput, pageURL string) ([]ExerciseAssignment, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	var assignments []ExerciseAssignment
	for _, row := range standardItems(root) {
		titleLink := firstDescendant(row, "a", "il-item-title")
		if titleLink == nil {
			continue
		}
		props := itemProperties(row)
		assignments = append(assignments, ExerciseAssignment{
			Title:          dom.Text(titleLink),
			URL:            mustHref(titleLink, pageURL),
			DueHint:        firstClassTextPtr(row, "col-sm-3"),
			DueAt:          stringPtrOrNil(props["Abgabetermin"]),
			Requirement:    stringPtrOrNil(props["Anforderung"]),
			LastSubmission: stringPtrOrNil(props["Datum der letzten Abgabe"]),
			SubmissionType: stringPtrOrNil(props["Type"]),
			Status:         stringPtrOrNil(props["Status"]),
			TeamActionURL:  firstButtonAction(row),
		})
	}
	if len(assignments) == 0 && !isAuthenticatedPage(htmlInput, pageURL) {
		return nil, errNotAuthenticated("exercise")
	}
	return assignments, nil
}

func isAuthenticatedPage(htmlInput, pageURL string) bool {
	parsed, err := url.Parse(pageURL)
	if err != nil || parsed.Host != "ovidius.uni-tuebingen.de" {
		return false
	}
	handOffMarkers := []string{"SAML" + "Response", "j_" + "username", "j_" + "password", "Login mit zentraler Universitäts-Kennung"}
	for _, marker := range handOffMarkers {
		if strings.Contains(htmlInput, marker) {
			return false
		}
	}
	for _, marker := range []string{
		"ILIAS Universität Tübingen",
		"logout.php",
		"il-mainbar-entries",
		"il-maincontrols-metabar",
		"baseClass=ilDashboardGUI",
		"baseClass=ilmembershipoverviewgui",
		"baseClass=ilderivedtasksgui",
	} {
		if strings.Contains(htmlInput, marker) {
			return true
		}
	}
	return false
}

func errNotAuthenticated(kind string) error {
	return &parseError{"the response did not look like an authenticated ILIAS " + kind + " page"}
}

type parseError struct{ message string }

func (e *parseError) Error() string { return e.message }

func standardItems(root *html.Node) []*html.Node {
	return dom.FindAll(root, func(node *html.Node) bool {
		return dom.IsElement(node, "div") && dom.HasClass(node, "il-item") && dom.HasClass(node, "il-std-item")
	})
}

func pageTitle(root *html.Node, fallback string) string {
	title := dom.FindFirst(root, func(node *html.Node) bool { return dom.IsElement(node, "title") })
	if title == nil || dom.Text(title) == "" {
		return fallback
	}
	return dom.Text(title)
}

func linkFromNode(node *html.Node, pageURL string) *Link {
	label := dom.Text(node)
	if label == "" {
		return nil
	}
	href, ok := dom.Attr(node, "href")
	if !ok || href == "" {
		return nil
	}
	return &Link{Label: label, URL: resolveURL(pageURL, href)}
}

func hasClassAncestor(node *html.Node, className string) bool {
	for parent := node.Parent; parent != nil; parent = parent.Parent {
		if dom.HasClass(parent, className) {
			return true
		}
	}
	return false
}

func containerBlockLabel(block *html.Node) string {
	header := dom.FindFirst(block, func(node *html.Node) bool {
		return dom.IsElement(node, "h2") && hasClassAncestor(node, "ilContainerBlockHeader")
	})
	return dom.Text(header)
}

func contentItem(row *html.Node, pageURL string) *ContentItem {
	titleLink := dom.FindFirst(row, func(node *html.Node) bool {
		if !dom.IsElement(node, "a") {
			return false
		}
		if dom.HasClass(node, "il_ContainerItemTitle") {
			return true
		}
		return hasClassAncestor(node, "il_ContainerItemTitle")
	})
	if titleLink == nil || dom.Text(titleLink) == "" {
		return nil
	}
	return &ContentItem{
		Label:      dom.Text(titleLink),
		URL:        mustHref(titleLink, pageURL),
		Kind:       firstImageAlt(row),
		Properties: classTexts(row, "il_ItemProperty"),
	}
}
