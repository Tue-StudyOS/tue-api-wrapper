package cli

import (
	"flag"
	"fmt"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/alma"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/config"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/env"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/output"
)

func runAlma(args []string) int {
	if len(args) == 0 {
		printAlmaUsage()
		return 1
	}

	switch args[0] {
	case "current-lectures":
		return runAlmaCurrentLectures(args[1:])
	case "exams":
		return runAlmaExams(args[1:])
	case "-h", "--help", "help":
		printAlmaUsage()
		return 0
	default:
		if _, ok := almaRoutes[args[0]]; ok {
			return runBackendRoute("alma "+args[0], almaRoutes[args[0]], args[1:])
		}
		return output.PrintError(fmt.Errorf("unknown alma command %q", args[0]))
	}
}

var almaRoutes = map[string]backendRoute{
	"timetable":               {Path: "/api/alma/timetable", Description: "Term timetable. Use --query term=...."},
	"enrollments":             {Path: "/api/alma/enrollments", Description: "Enrollment page payload."},
	"catalog":                 {Path: "/api/alma/catalog", Description: "Authenticated Alma catalog nodes. Optional queries: term, limit."},
	"module-search":           {Path: "/api/alma/module-search", Description: "Public module search. Pass filters through repeated --query flags."},
	"module-search-filters":   {Path: "/api/alma/module-search/filters", Description: "Valid public module-search filter values."},
	"module-detail":           {Path: "/api/alma/module-detail", Description: "Public module detail. Use --query url=...."},
	"documents":               {Path: "/api/alma/documents", Description: "Study-service report list."},
	"studyservice":            {Path: "/api/alma/studyservice", Description: "Legacy study-service summary contract."},
	"current-document":        {Path: "/api/alma/documents/current", Description: "Current study-service PDF. Use --output file.pdf."},
	"document":                {Path: "/api/alma/documents/{doc_id}", PathArgs: []string{"doc_id"}, Description: "Study-service PDF by document id. Use --output file.pdf."},
	"document-download-url":   {Path: "/api/alma/documents/{doc_id}/download-url", PathArgs: []string{"doc_id"}, Description: "Relative download URL for a study-service PDF."},
	"exam-report":             {Method: "POST", Path: "/api/alma/exams/report", Description: "Generate an official Alma exam report PDF. Use --output file.pdf and optional --query trigger_name=...."},
	"exam-reports":            {Path: "/api/alma/exams/reports", Description: "Available official Alma exam report actions."},
	"current-lectures-api":    {Path: "/api/alma/current-lectures", Description: "Backend current-lectures view. Optional queries: date, limit."},
	"course-register":         {Method: "POST", Path: "/api/alma/course-registration", Description: "Register for an Alma course when the detail page supports it. Use --query url=... and optional planelement_id=...."},
	"course-register-options": {Method: "POST", Path: "/api/alma/course-registration/options", Description: "Open Alma's registration chooser and list available registration paths. Use --query url=...."},
	"course-register-support": {Path: "/api/alma/course-registration/support", Description: "Check whether an Alma detail page exposes a registration action. Use --query url=...."},
	"timetable-controls":      {Path: "/api/alma/timetable/controls", Description: "Timetable controls and term options."},
	"timetable-view":          {Path: "/api/alma/timetable/view", Description: "Rendered timetable view. Optional queries: term, week, from_date, to_date, single_day, limit."},
	"timetable-assignments":   {Path: "/api/alma/timetable/course-assignments", Description: "Current timetable courses with Alma module and degree assignments."},
	"timetable-pdf":           {Path: "/api/alma/timetable/pdf", Description: "Timetable PDF. Use --output timetable.pdf and optional term/week/date queries."},
	"portal-messages-feed":    {Path: "/api/alma/portal-messages/feed", Description: "Portal messages feed."},
	"study-planner":           {Path: "/api/alma/study-planner", Description: "Study planner grid and modules."},
	"course-search":           {Path: "/api/alma/course-search", Description: "Authenticated course search. Optional queries: query, term, limit."},
	"catalog-page":            {Path: "/api/alma/catalog/page", Description: "Authenticated catalog page with section structure. Optional queries: term, limit."},
	"studyservice-report":     {Method: "POST", Path: "/api/alma/studyservice/report", Description: "Generate an official Alma study-service PDF. Use --output file.pdf and optional trigger_name/term_id queries."},
	"studyservice-summary":    {Path: "/api/alma/studyservice/summary", Description: "Expanded study-service summary with tabs and output requests."},
}

func printAlmaUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue alma current-lectures [--date DD.MM.YYYY] [--limit N] [--json]")
	fmt.Println("  tue alma exams [--limit N|--query limit=N]")
	fmt.Println("  tue alma <backend-command> [--query key=value ...] [--output PATH] [--raw]")
	fmt.Println()
	fmt.Println("Backend-backed commands:")
	printBackendGroupUsage("alma", almaRoutes)
}

func runAlmaExams(args []string) int {
	fs := flag.NewFlagSet("alma exams", flag.ContinueOnError)
	limit := fs.Int("limit", 50, "Maximum exam rows")
	fs.Bool("raw", false, "Accepted for backend CLI compatibility; output is JSON either way")
	query := multiValueFlag{}
	fs.Var(&query, "query", "key=value query value")
	if err := fs.Parse(args); err != nil {
		return 1
	}
	if fs.NArg() != 0 {
		return output.PrintError(fmt.Errorf("unexpected argument %q", fs.Arg(0)))
	}
	if queryLimit := query.first("limit"); queryLimit != "" {
		parsed, err := parsePositiveInt(queryLimit)
		if err != nil {
			return output.PrintError(fmt.Errorf("invalid limit query value %q", queryLimit))
		}
		*limit = parsed
	}

	client, ok := authenticatedAlmaClient()
	if !ok {
		return 1
	}
	return printNativeJSON(client.FetchExamOverview(*limit))
}

func runAlmaCurrentLectures(args []string) int {
	fs := flag.NewFlagSet("alma current-lectures", flag.ContinueOnError)
	date := fs.String("date", "", "Alma date filter in DD.MM.YYYY format")
	limit := fs.Int("limit", 50, "Maximum number of rows to return")
	asJSON := fs.Bool("json", false, "Print JSON instead of text")
	if err := fs.Parse(args); err != nil {
		return 1
	}

	client, ok := authenticatedAlmaClient()
	if !ok {
		return 1
	}

	page, err := client.FetchCurrentLectures(*date, *limit)
	if err != nil {
		return output.PrintError(err)
	}

	if *asJSON {
		if err := output.PrintJSON(page); err != nil {
			return output.PrintError(err)
		}
		return 0
	}

	selectedDate := "-"
	if page.SelectedDate != nil {
		selectedDate = *page.SelectedDate
	}
	fmt.Printf("Date: %s\n", selectedDate)
	fmt.Printf("Results: %d\n", len(page.Results))
	for index, item := range page.Results {
		start := valueOr(item.Start, "-")
		end := valueOr(item.End, "-")
		room := valueOr(item.Room, "-")
		fmt.Printf("%02d. %s - %s | %s | %s\n", index+1, start, end, item.Title, room)
	}
	return 0
}

func authenticatedAlmaClient() (*alma.Client, bool) {
	username, password := env.AlmaCredentials()
	if username == "" || password == "" {
		output.PrintError(fmt.Errorf(
			"set UNI_USERNAME and UNI_PASSWORD before using authenticated commands; legacy ALMA_* and ILIAS_* env vars are still supported as fallbacks",
		))
		return nil, false
	}
	client, err := alma.NewClient(config.DefaultTimeout())
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

func valueOr(value *string, fallback string) string {
	if value == nil || *value == "" {
		return fallback
	}
	return *value
}
