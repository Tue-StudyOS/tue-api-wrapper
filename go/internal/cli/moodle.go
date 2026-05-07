package cli

import (
	"encoding/json"
	"flag"
	"fmt"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/config"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/env"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/moodle"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/output"
)

func runMoodle(args []string) int {
	if len(args) == 0 || args[0] == "-h" || args[0] == "--help" || args[0] == "help" {
		printMoodleUsage()
		if len(args) == 0 {
			return 1
		}
		return 0
	}

	client, ok := authenticatedMoodleClient()
	if !ok {
		return 1
	}

	switch args[0] {
	case "dashboard":
		return runMoodleDashboard(args[1:], client)
	case "calendar":
		return runMoodleCalendar(args[1:], client)
	case "courses":
		return runMoodleCourses(args[1:], client)
	case "categories":
		return printNativeJSON(client.FetchCategories())
	case "category":
		return runMoodleCategory(args[1:], client)
	case "category-courses":
		return runMoodleCategory(args[1:], client)
	case "course":
		return runMoodleCourse(args[1:], client)
	case "course-enrolment":
		return runMoodleCourse(args[1:], client)
	case "course-enrol":
		return runMoodleCourseEnrol(args[1:], client)
	case "grades":
		return runMoodleGrades(args[1:], client)
	case "messages":
		return printNativeJSON(client.FetchMessages())
	case "notifications":
		return printNativeJSON(client.FetchNotifications())
	default:
		return output.PrintError(fmt.Errorf("unknown moodle command %q", args[0]))
	}
}

func printMoodleUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue moodle dashboard [--event-limit N] [--course-limit N] [--recent-limit N]")
	fmt.Println("  tue moodle calendar [--days N] [--limit N]")
	fmt.Println("  tue moodle courses [--classification all|inprogress|future|past] [--limit N] [--offset N]")
	fmt.Println("  tue moodle categories")
	fmt.Println("  tue moodle category <category_id>")
	fmt.Println("  tue moodle course <course_id>")
	fmt.Println("  tue moodle course-enrolment <course_id>")
	fmt.Println("  tue moodle course-enrol <course_id> [--query enrolment_key=VALUE]")
	fmt.Println("  tue moodle grades [--limit N]")
	fmt.Println("  tue moodle messages")
	fmt.Println("  tue moodle notifications")
}

func authenticatedMoodleClient() (*moodle.Client, bool) {
	username, password := env.AlmaCredentials()
	if username == "" || password == "" {
		output.PrintError(fmt.Errorf("set UNI_USERNAME and UNI_PASSWORD before using authenticated Moodle commands"))
		return nil, false
	}
	client, err := moodle.NewClient(config.DefaultTimeout())
	if err != nil {
		output.PrintError(err)
		return nil, false
	}
	if err := client.Login(username, password); err != nil {
		output.PrintError(err)
		return nil, false
	}
	return client, true
}

func printNativeJSON(value any, err error) int {
	if err != nil {
		return output.PrintError(err)
	}
	if err := output.PrintJSON(value); err != nil {
		return output.PrintError(err)
	}
	return 0
}

func runMoodleGrades(args []string, client *moodle.Client) int {
	fs := flag.NewFlagSet("moodle grades", flag.ContinueOnError)
	limit := fs.Int("limit", 50, "Maximum grade rows")
	if err := fs.Parse(args); err != nil {
		return 1
	}
	return printNativeJSON(client.FetchGrades(*limit))
}

func runMoodleDashboard(args []string, client *moodle.Client) int {
	fs := flag.NewFlagSet("moodle dashboard", flag.ContinueOnError)
	eventLimit := fs.Int("event-limit", 6, "Maximum calendar events")
	courseLimit := fs.Int("course-limit", 12, "Maximum courses")
	recentLimit := fs.Int("recent-limit", 9, "Maximum recent items")
	if err := fs.Parse(args); err != nil {
		return 1
	}
	return printNativeJSON(client.FetchDashboard(*eventLimit, *courseLimit, *recentLimit))
}

func runMoodleCalendar(args []string, client *moodle.Client) int {
	fs := flag.NewFlagSet("moodle calendar", flag.ContinueOnError)
	days := fs.Int("days", 30, "Number of days")
	limit := fs.Int("limit", 50, "Maximum events")
	if err := fs.Parse(args); err != nil {
		return 1
	}
	return printNativeJSON(client.FetchCalendar(*days, *limit))
}

func runMoodleCourses(args []string, client *moodle.Client) int {
	fs := flag.NewFlagSet("moodle courses", flag.ContinueOnError)
	classification := fs.String("classification", "all", "Course classification")
	limit := fs.Int("limit", 24, "Maximum courses")
	offset := fs.Int("offset", 0, "Course offset")
	if err := fs.Parse(args); err != nil {
		return 1
	}
	return printNativeJSON(client.FetchCourses(*limit, *offset, *classification))
}

func runMoodleCategory(args []string, client *moodle.Client) int {
	if len(args) != 1 {
		return output.PrintError(fmt.Errorf("usage: tue moodle category <category_id>"))
	}
	return printNativeJSON(client.FetchCategory(args[0]))
}

func runMoodleCourse(args []string, client *moodle.Client) int {
	if len(args) != 1 {
		return output.PrintError(fmt.Errorf("usage: tue moodle course <course_id>"))
	}
	return printNativeJSON(client.FetchCourse(args[0]))
}

func runMoodleCourseEnrol(args []string, client *moodle.Client) int {
	fs := flag.NewFlagSet("moodle course-enrol", flag.ContinueOnError)
	query := multiValueFlag{}
	fs.Var(&query, "query", "key=value query value")
	if err := fs.Parse(args); err != nil {
		return 1
	}
	if fs.NArg() != 1 {
		return output.PrintError(fmt.Errorf("usage: tue moodle course-enrol <course_id> [--query enrolment_key=VALUE]"))
	}
	return printNativeJSON(client.EnrolCourse(fs.Arg(0), query.first("enrolment_key")))
}

type multiValueFlag []string

func (f *multiValueFlag) String() string {
	data, _ := json.Marshal([]string(*f))
	return string(data)
}

func (f *multiValueFlag) Set(value string) error {
	*f = append(*f, value)
	return nil
}

func (f multiValueFlag) first(key string) string {
	prefix := key + "="
	for _, value := range f {
		if len(value) >= len(prefix) && value[:len(prefix)] == prefix {
			return value[len(prefix):]
		}
	}
	return ""
}
