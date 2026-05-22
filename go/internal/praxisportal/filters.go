package praxisportal

import (
	"fmt"
	"strings"
	"time"
)

func buildVisibilityFilter(now time.Time) string {
	dayStart := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location()).Unix() - 100
	dayEnd := time.Date(now.Year(), now.Month(), now.Day(), 23, 59, 59, 0, now.Location()).Unix() + 100
	return fmt.Sprintf(
		"(blocked<1 AND hidden<1 AND project_stop_date>=%d AND project_start_date<=%d) AND (visible_institutes:-1)",
		dayStart,
		dayEnd,
	)
}

func buildFilterExpression(base string, projectTypeIDs []int, industryIDs []int) string {
	clauses := []string{base}
	if len(projectTypeIDs) > 0 {
		items := make([]string, 0, len(projectTypeIDs))
		for _, value := range projectTypeIDs {
			items = append(items, fmt.Sprintf("project_type.id:%d", value))
		}
		clauses = append(clauses, "("+strings.Join(items, " OR ")+")")
	}
	if len(industryIDs) > 0 {
		items := make([]string, 0, len(industryIDs))
		for _, value := range industryIDs {
			items = append(items, fmt.Sprintf("industry.id:%d", value))
		}
		clauses = append(clauses, "("+strings.Join(items, " OR ")+")")
	}
	return strings.Join(clauses, " AND ")
}
