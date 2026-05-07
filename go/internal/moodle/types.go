package moodle

type GradesPage struct {
	SourceURL string      `json:"source_url"`
	Items     []GradeItem `json:"items"`
}

type GradeItem struct {
	CourseTitle string  `json:"course_title"`
	Grade       *string `json:"grade,omitempty"`
	Percentage  *string `json:"percentage,omitempty"`
	RangeHint   *string `json:"range_hint,omitempty"`
	Rank        *string `json:"rank,omitempty"`
	Feedback    *string `json:"feedback,omitempty"`
	URL         *string `json:"url,omitempty"`
}

type FeedPage struct {
	SourceURL string     `json:"source_url"`
	Items     []FeedItem `json:"items"`
}

type FeedItem struct {
	Title     string  `json:"title"`
	Body      *string `json:"body,omitempty"`
	Preview   *string `json:"preview,omitempty"`
	Sender    *string `json:"sender,omitempty"`
	Timestamp *string `json:"timestamp,omitempty"`
	URL       *string `json:"url,omitempty"`
	Unread    *bool   `json:"unread,omitempty"`
}

type CoursesPage struct {
	SourceURL  string           `json:"source_url"`
	Items      []map[string]any `json:"items"`
	NextOffset *int             `json:"next_offset,omitempty"`
}

type DashboardPage struct {
	SourceURL string           `json:"source_url"`
	Events    []map[string]any `json:"events"`
	Recent    []map[string]any `json:"recent_items"`
	Courses   []map[string]any `json:"courses"`
}

type CalendarPage struct {
	SourceURL string           `json:"source_url"`
	Items     []map[string]any `json:"items"`
}

type CategoryPage struct {
	SourceURL  string           `json:"source_url"`
	Title      string           `json:"title"`
	Categories []CategoryItem   `json:"categories"`
	Courses    []map[string]any `json:"courses"`
}

type CategoryItem struct {
	ID          *int    `json:"id,omitempty"`
	Title       string  `json:"title"`
	URL         *string `json:"url,omitempty"`
	Description *string `json:"description,omitempty"`
}

type CourseDetail struct {
	SourceURL              string            `json:"source_url"`
	ID                     *int              `json:"id,omitempty"`
	Title                  string            `json:"title"`
	CourseURL              *string           `json:"course_url,omitempty"`
	Summary                *string           `json:"summary,omitempty"`
	Teachers               []string          `json:"teachers,omitempty"`
	SelfEnrolmentAvailable bool              `json:"self_enrolment_available"`
	RequiresEnrolmentKey   bool              `json:"requires_enrolment_key"`
	EnrolmentActionURL     *string           `json:"enrolment_action_url,omitempty"`
	EnrolmentPayload       map[string]string `json:"enrolment_payload,omitempty"`
	EnrolmentKeyFieldName  *string           `json:"enrolment_key_field_name,omitempty"`
	EnrolmentLabel         *string           `json:"enrolment_label,omitempty"`
	NoEnrolmentKeyRequired bool              `json:"no_enrolment_key_required"`
}

type EnrolmentResult struct {
	Success   bool    `json:"success"`
	PageURL   string  `json:"page_url"`
	CourseID  int     `json:"course_id"`
	CourseURL *string `json:"course_url,omitempty"`
	Message   *string `json:"message,omitempty"`
}
