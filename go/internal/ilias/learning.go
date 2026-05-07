package ilias

import (
	"fmt"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/dom"
	"golang.org/x/net/html"
)

const (
	iliasRootURL        = "https://ovidius.uni-tuebingen.de/ilias3/goto.php/root/1"
	iliasMembershipURL  = "https://ovidius.uni-tuebingen.de/ilias3/ilias.php?baseClass=ilmembershipoverviewgui"
	iliasDerivedTaskURL = "https://ovidius.uni-tuebingen.de/ilias3/ilias.php?baseClass=ilderivedtasksgui"
)

func (c *Client) FetchRootPage() (*RootPage, error) {
	resp, body, err := c.http.Get(iliasRootURL)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	return parseRootPage(string(body), resp.Request.URL.String())
}

func (c *Client) FetchContentPage(target string) (*ContentPage, error) {
	return c.fetchContentLike(target, parseContentPage)
}

func (c *Client) FetchForumTopics(target string) ([]ForumTopic, error) {
	return fetchSliceLike(c, target, parseForumTopics)
}

func (c *Client) FetchExerciseAssignments(target string) ([]ExerciseAssignment, error) {
	return fetchSliceLike(c, target, parseExerciseAssignments)
}

func (c *Client) FetchMembershipOverview(limit int) ([]MembershipItem, error) {
	resp, body, err := c.http.Get(iliasMembershipURL)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	items, err := parseMembershipOverview(string(body), resp.Request.URL.String())
	if err != nil {
		return nil, err
	}
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func (c *Client) FetchTaskOverview(limit int) ([]TaskItem, error) {
	resp, body, err := c.http.Get(iliasDerivedTaskURL)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	items, err := parseTaskOverview(string(body), resp.Request.URL.String())
	if err != nil {
		return nil, err
	}
	if limit > 0 && len(items) > limit {
		items = items[:limit]
	}
	return items, nil
}

func (c *Client) fetchContentLike(target string, parser func(string, string) (*ContentPage, error)) (*ContentPage, error) {
	targetURL, err := normalizeTargetURL(target)
	if err != nil {
		return nil, err
	}
	resp, body, err := c.http.Get(targetURL)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	return parser(string(body), resp.Request.URL.String())
}

func fetchSliceLike[T any](c *Client, target string, parser func(string, string) ([]T, error)) ([]T, error) {
	targetURL, err := normalizeTargetURL(target)
	if err != nil {
		return nil, err
	}
	resp, body, err := c.http.Get(targetURL)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	return parser(string(body), resp.Request.URL.String())
}

func normalizeTargetURL(target string) (string, error) {
	value := strings.TrimSpace(target)
	if value == "" {
		return "", fmt.Errorf("a non-empty ILIAS target is required")
	}
	if strings.HasPrefix(value, "http://") || strings.HasPrefix(value, "https://") {
		return value, nil
	}
	if strings.HasPrefix(value, "goto.php/") {
		return resolveURL("https://ovidius.uni-tuebingen.de/ilias3/", value), nil
	}
	return resolveURL("https://ovidius.uni-tuebingen.de/ilias3/goto.php/", strings.TrimLeft(value, "/")), nil
}

func parseRootPage(htmlInput, pageURL string) (*RootPage, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	page := &RootPage{Title: pageTitle(root, "ILIAS")}
	for _, link := range dom.FindAll(root, func(node *html.Node) bool {
		return dom.IsElement(node, "a") && hasClassAncestor(node, "il-mainbar-entries")
	}) {
		if item := linkFromNode(link, pageURL); item != nil {
			page.MainbarLinks = append(page.MainbarLinks, *item)
		}
	}
	for _, link := range dom.FindAll(root, func(node *html.Node) bool {
		return dom.IsElement(node, "a") && dom.HasClass(node, "il_ContainerItemTitle")
	}) {
		if item := linkFromNode(link, pageURL); item != nil {
			page.TopCategories = append(page.TopCategories, *item)
		}
	}
	if len(page.TopCategories) == 0 && !isAuthenticatedPage(htmlInput, pageURL) {
		return nil, fmt.Errorf("the response did not look like an authenticated ILIAS root page")
	}
	return page, nil
}

func parseContentPage(htmlInput, pageURL string) (*ContentPage, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	page := &ContentPage{Title: pageTitle(root, "ILIAS"), PageURL: pageURL}
	for _, block := range dom.FindAll(root, func(node *html.Node) bool {
		return dom.IsElement(node, "div") && dom.HasClass(node, "ilContainerBlock")
	}) {
		label := containerBlockLabel(block)
		var items []ContentItem
		for _, row := range dom.FindAll(block, func(node *html.Node) bool {
			return dom.IsElement(node, "div") && dom.HasClass(node, "ilContainerListItemOuter")
		}) {
			if item := contentItem(row, pageURL); item != nil {
				items = append(items, *item)
			}
		}
		if label != "" && len(items) > 0 {
			page.Sections = append(page.Sections, ContentSection{Label: label, Items: items})
		}
	}
	if len(page.Sections) == 0 && !isAuthenticatedPage(htmlInput, pageURL) {
		return nil, fmt.Errorf("the response did not look like an authenticated ILIAS content page")
	}
	return page, nil
}

func parseMembershipOverview(htmlInput, pageURL string) ([]MembershipItem, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	var items []MembershipItem
	for _, row := range standardItems(root) {
		titleLink := firstDescendant(row, "a", "il-item-title")
		if titleLink == nil {
			continue
		}
		title := dom.Text(titleLink)
		if title == "" {
			continue
		}
		item := MembershipItem{Title: title, URL: mustHref(titleLink, pageURL), Properties: propertyLines(row)}
		item.Kind = firstImageAlt(row)
		item.Description = classTextPtr(row, "il-item-description")
		if button := firstButtonAction(row); button != nil {
			item.InfoURL = button
		}
		items = append(items, item)
	}
	if len(items) == 0 && !isAuthenticatedPage(htmlInput, pageURL) {
		return nil, fmt.Errorf("the response did not look like an authenticated ILIAS membership overview")
	}
	return items, nil
}

func parseTaskOverview(htmlInput, pageURL string) ([]TaskItem, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	var items []TaskItem
	for _, row := range standardItems(root) {
		titleNode := firstDescendant(row, "a", "il-item-title")
		if titleNode == nil {
			titleNode = firstDescendant(row, "button", "il-item-title")
		}
		if titleNode == nil {
			continue
		}
		target := hrefOrAction(titleNode, pageURL)
		if target == "" {
			continue
		}
		properties := itemProperties(row)
		items = append(items, TaskItem{
			Title:    dom.Text(titleNode),
			URL:      target,
			ItemType: firstMapValue(properties, "Übung", "Kurs", "Typ"),
			Start:    stringPtrOrNil(properties["Beginn"]),
			End:      stringPtrOrNil(properties["Ende"]),
		})
	}
	if len(items) == 0 && !isAuthenticatedPage(htmlInput, pageURL) {
		return nil, fmt.Errorf("the response did not look like an authenticated ILIAS task overview")
	}
	return items, nil
}
