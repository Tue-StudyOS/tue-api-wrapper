package alma

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/config"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/dom"
	"golang.org/x/net/html"
)

const examOverviewPath = "/alma/pages/sul/examAssessment/personExamsReadonly.xhtml?_flowId=examsOverviewForPerson-flow&navigationPosition=hisinoneMeinStudium%2CexamAssessmentForStudent&recordRequest=true"

var examLevelPattern = regexp.MustCompile(`treeTableCellLevel(\d+)`)

func (c *Client) FetchExamOverview(limit int) ([]ExamNode, error) {
	resp, body, err := c.http.Get(config.AlmaBaseURL + examOverviewPath)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	htmlInput := string(body)
	if looksLoggedOut(htmlInput) {
		return nil, fmt.Errorf("session is not authenticated; the exam overview page redirected back to login")
	}

	rows, err := parseExamOverview(htmlInput)
	if err != nil {
		return nil, err
	}
	if limit > 0 && len(rows) > limit {
		rows = rows[:limit]
	}
	return rows, nil
}

func parseExamOverview(htmlInput string) ([]ExamNode, error) {
	root, err := dom.Parse(htmlInput)
	if err != nil {
		return nil, err
	}
	table := dom.FindFirst(root, func(node *html.Node) bool {
		return dom.IsElement(node, "table") && dom.HasClass(node, "treeTableWithIcons")
	})
	if table == nil {
		return nil, fmt.Errorf("could not find the Alma exam overview tree table")
	}

	var rows []ExamNode
	for _, row := range dom.FindAll(table, func(node *html.Node) bool { return dom.IsElement(node, "tr") }) {
		level, ok := examRowLevel(row)
		if !ok || len(findChildren(row, "td")) < 10 {
			continue
		}
		titleNode := dom.FindFirst(row, func(node *html.Node) bool {
			id, ok := dom.Attr(node, "id")
			return ok && (strings.HasSuffix(id, ":defaulttext") || strings.HasSuffix(id, ":unDeftxt"))
		})
		if titleNode == nil {
			continue
		}

		rows = append(rows, ExamNode{
			Level:       level,
			Kind:        examKind(row),
			Title:       dom.Text(titleNode),
			Number:      examField(row, "elementnr"),
			Attempt:     examField(row, "attempt"),
			Grade:       examField(row, "grade"),
			CP:          examField(row, "bonus"),
			Malus:       examField(row, "malus"),
			Status:      examField(row, "workstatus"),
			FreeTrial:   examField(row, "freeTrial"),
			Remark:      examField(row, "remark"),
			Exception:   firstString(examField(row, "exceptionNein"), examField(row, "exceptionJa")),
			ReleaseDate: examField(row, "geplantesFreigabedatum"),
		})
	}
	return rows, nil
}

func examRowLevel(row *html.Node) (int, bool) {
	classValue, ok := dom.Attr(row, "class")
	if !ok {
		return 0, false
	}
	for _, className := range strings.Fields(classValue) {
		matches := examLevelPattern.FindStringSubmatch(className)
		if len(matches) != 2 {
			continue
		}
		level, err := strconv.Atoi(matches[1])
		return level, err == nil
	}
	return 0, false
}

func examKind(row *html.Node) *string {
	icon := dom.FindFirst(row, func(node *html.Node) bool {
		return dom.IsElement(node, "img") && dom.HasClass(node, "submitImageTable")
	})
	if icon == nil {
		return nil
	}
	value, ok := dom.Attr(icon, "alt")
	if !ok || strings.TrimSpace(value) == "" {
		return nil
	}
	return stringPtr(dom.NormalizeSpace(value))
}

func examField(row *html.Node, suffix string) *string {
	node := dom.FindFirst(row, func(node *html.Node) bool {
		id, ok := dom.Attr(node, "id")
		return ok && strings.HasSuffix(id, ":"+suffix)
	})
	if node == nil {
		return nil
	}
	value := dom.Text(node)
	if value == "" {
		return nil
	}
	return stringPtr(value)
}

func firstString(values ...*string) *string {
	for _, value := range values {
		if value != nil && *value != "" {
			return value
		}
	}
	return nil
}
