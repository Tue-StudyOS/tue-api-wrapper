package cli

var moodleRoutes = map[string]backendRoute{
	"dashboard": {
		Path:        "/api/moodle/dashboard",
		Description: "Moodle dashboard. Optional queries: event_limit, course_limit, recent_limit.",
	},
	"calendar": {
		Path:        "/api/moodle/calendar",
		Description: "Moodle calendar. Optional queries: days, limit.",
	},
	"courses": {
		Path:        "/api/moodle/courses",
		Description: "Enrolled Moodle courses. Optional queries: classification, limit, offset.",
	},
	"categories": {
		Path:        "/api/moodle/categories",
		Description: "Root Moodle categories.",
	},
	"category": {
		Path:        "/api/moodle/categories/{category_id}",
		PathArgs:    []string{"category_id"},
		Description: "Single Moodle category detail.",
	},
	"category-courses": {
		Path:        "/api/moodle/categories/{category_id}/courses",
		PathArgs:    []string{"category_id"},
		Description: "Courses inside a Moodle category.",
	},
	"course": {
		Path:        "/api/moodle/course/{course_id}",
		PathArgs:    []string{"course_id"},
		Description: "Single Moodle course detail.",
	},
	"course-enrolment": {
		Path:        "/api/moodle/course/{course_id}/enrolment",
		PathArgs:    []string{"course_id"},
		Description: "Read-only Moodle enrolment state for a course.",
	},
	"course-enrol": {
		Method:      "POST",
		Path:        "/api/moodle/course/{course_id}/enrol",
		PathArgs:    []string{"course_id"},
		Description: "Enroll in a Moodle course. Use --query enrolment_key=... when required.",
	},
	"grades": {
		Path:        "/api/moodle/grades",
		Description: "Moodle grades. Optional query: limit.",
	},
	"messages": {
		Path:        "/api/moodle/messages",
		Description: "Moodle messages. Optional query: limit.",
	},
	"notifications": {
		Path:        "/api/moodle/notifications",
		Description: "Moodle notifications. Optional query: limit.",
	},
}

func runMoodle(args []string) int {
	return runBackendGroup("moodle", args, moodleRoutes)
}
