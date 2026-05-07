package moodle

import (
	"fmt"
	"time"
)

func (c *Client) FetchGrades(limit int) (*GradesPage, error) {
	html, pageURL, err := c.authenticatedPage(c.baseURL + "/grade/report/overview/index.php")
	if err != nil {
		return nil, err
	}
	return parseGradesPage(html, pageURL, limit)
}

func (c *Client) FetchMessages() (*FeedPage, error) {
	html, pageURL, err := c.authenticatedPage(c.baseURL + "/message/index.php")
	if err != nil {
		return nil, err
	}
	return parseFeedPage(html, pageURL, []string{".list-group-item", ".message", ".conversation", "li"})
}

func (c *Client) FetchNotifications() (*FeedPage, error) {
	html, pageURL, err := c.authenticatedPage(c.baseURL + "/message/output/popup/notifications.php")
	if err != nil {
		return nil, err
	}
	return parseFeedPage(html, pageURL, []string{".notification", ".content-item-container", "table.generaltable tbody tr", "li"})
}

func (c *Client) FetchCategories() (*CategoryPage, error) {
	html, pageURL, err := c.authenticatedPage(c.baseURL)
	if err != nil {
		return nil, err
	}
	return parseCategoryPage(html, pageURL)
}

func (c *Client) FetchCategory(categoryID string) (*CategoryPage, error) {
	html, pageURL, err := c.authenticatedPage(c.baseURL + "/course/index.php?categoryid=" + categoryID)
	if err != nil {
		return nil, err
	}
	return parseCategoryPage(html, pageURL)
}

func (c *Client) FetchCourse(courseID string) (*CourseDetail, error) {
	html, pageURL, err := c.authenticatedPage(c.baseURL + "/enrol/index.php?id=" + courseID)
	if err != nil {
		return nil, err
	}
	return parseCourseDetail(html, pageURL)
}

func (c *Client) EnrolCourse(courseID, enrolmentKey string) (*EnrolmentResult, error) {
	detail, err := c.FetchCourse(courseID)
	if err != nil {
		return nil, err
	}
	if detail.EnrolmentActionURL == nil || len(detail.EnrolmentPayload) == 0 {
		return nil, fmt.Errorf("Moodle did not expose a self-enrol form for this course")
	}
	if detail.RequiresEnrolmentKey && enrolmentKey == "" {
		return nil, fmt.Errorf("this Moodle course requires an enrolment key")
	}
	payload := cloneMapValues(detail.EnrolmentPayload)
	if detail.EnrolmentKeyFieldName != nil && enrolmentKey != "" {
		payload.Set(*detail.EnrolmentKeyFieldName, enrolmentKey)
	}
	payload.Set("submitbutton", "Einschreiben")
	resp, body, err := c.http.PostForm(*detail.EnrolmentActionURL, payload)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	pageURL := resp.Request.URL.String()
	message := extractPageMessage(string(body))
	return &EnrolmentResult{
		Success:   isKnownContentPath(resp.Request.URL.Path) && message == nil,
		PageURL:   pageURL,
		CourseID:  valueInt(detail.ID),
		CourseURL: detail.CourseURL,
		Message:   message,
	}, nil
}

func (c *Client) FetchDashboard(eventLimit, courseLimit, recentLimit int) (*DashboardPage, error) {
	html, pageURL, err := c.authenticatedPage(c.baseURL + "/my/")
	if err != nil {
		return nil, err
	}
	cfg, err := extractPageConfig(html)
	if err != nil {
		return nil, err
	}
	now := time.Now()
	events, err := c.ajax(pageURL, cfg.Sesskey, "core_calendar_get_action_events_by_timesort", map[string]any{
		"limitnum": eventLimit, "timesortfrom": now.Unix(), "timesortto": now.Add(30 * 24 * time.Hour).Unix(), "limittononsuspendedevents": true,
	})
	if err != nil {
		return nil, err
	}
	recent, err := c.ajax(pageURL, cfg.Sesskey, "block_recentlyaccesseditems_get_recent_items", map[string]any{"limit": recentLimit})
	if err != nil {
		return nil, err
	}
	courses, err := c.coursesPayload(pageURL, cfg.Sesskey, courseLimit, 0, "all")
	if err != nil {
		return nil, err
	}
	return &DashboardPage{SourceURL: pageURL, Events: asItems(events), Recent: asItems(recent), Courses: asItems(courses)}, nil
}

func (c *Client) FetchCalendar(days, limit int) (*CalendarPage, error) {
	html, pageURL, err := c.authenticatedPage(c.baseURL + "/my/")
	if err != nil {
		return nil, err
	}
	cfg, err := extractPageConfig(html)
	if err != nil {
		return nil, err
	}
	now := time.Now()
	payload, err := c.ajax(pageURL, cfg.Sesskey, "core_calendar_get_action_events_by_timesort", map[string]any{
		"limitnum": limit, "timesortfrom": now.Unix(), "timesortto": now.Add(time.Duration(days) * 24 * time.Hour).Unix(), "limittononsuspendedevents": true,
	})
	if err != nil {
		return nil, err
	}
	return &CalendarPage{SourceURL: pageURL, Items: asItems(payload)}, nil
}

func (c *Client) FetchCourses(limit, offset int, classification string) (*CoursesPage, error) {
	html, pageURL, err := c.authenticatedPage(c.baseURL + "/my/courses.php")
	if err != nil {
		return nil, err
	}
	cfg, err := extractPageConfig(html)
	if err != nil {
		return nil, err
	}
	payload, err := c.coursesPayload(pageURL, cfg.Sesskey, limit, offset, classification)
	if err != nil {
		return nil, err
	}
	return &CoursesPage{SourceURL: pageURL, Items: asItems(payload), NextOffset: nextOffset(payload)}, nil
}

func (c *Client) coursesPayload(pageURL, sesskey string, limit, offset int, classification string) (any, error) {
	return c.ajax(pageURL, sesskey, "core_course_get_enrolled_courses_by_timeline_classification", map[string]any{
		"offset": offset, "limit": limit, "classification": classification, "sort": "fullname",
		"customfieldname": "", "customfieldvalue": "",
		"requiredfields": []string{"id", "fullname", "shortname", "showcoursecategory", "showshortname", "visible", "enddate"},
	})
}
