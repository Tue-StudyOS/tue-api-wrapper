package cli

import (
	"flag"
	"fmt"
	"os"
	"strings"

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
	case "timetable":
		return runAlmaTimetable(args[1:])
	case "-h", "--help", "help":
		printAlmaUsage()
		return 0
	default:
		return output.PrintError(fmt.Errorf("unknown alma command %q", args[0]))
	}
}

func printAlmaUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue alma current-lectures [--date DD.MM.YYYY] [--limit N] [--json]")
	fmt.Println("  tue alma exams [--limit N|--query limit=N]")
	fmt.Println("  tue alma timetable [--term TERM] [--query term=TERM] [--ics] [--output PATH] [--raw]")
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

func runAlmaTimetable(args []string) int {
	fs := flag.NewFlagSet("alma timetable", flag.ContinueOnError)
	term := fs.String("term", "", "Timetable term label, e.g. \"Sommersemester 2026\"")
	icsOutput := fs.Bool("ics", false, "Print the raw iCalendar payload instead of JSON")
	outputPath := fs.String("output", "", "Write the iCalendar payload to a file (use with --ics)")
	fs.Bool("raw", false, "Accepted for backend CLI compatibility; has no effect for native commands")
	query := multiValueFlag{}
	fs.Var(&query, "query", "key=value query value")
	if err := fs.Parse(args); err != nil {
		return 1
	}
	if fs.NArg() != 0 {
		return output.PrintError(fmt.Errorf("unexpected argument %q", fs.Arg(0)))
	}

	resolvedTerm := strings.TrimSpace(*term)
	if queryTerm := strings.TrimSpace(query.first("term")); queryTerm != "" {
		resolvedTerm = queryTerm
	}
	if resolvedTerm == "" {
		resolvedTerm = "Sommer 2026"
	}

	client, ok := authenticatedAlmaClient()
	if !ok {
		return 1
	}

	result, err := client.FetchTimetableForTerm(resolvedTerm)
	if err != nil {
		return output.PrintError(err)
	}

	if *icsOutput || *outputPath != "" {
		if *outputPath != "" {
			if err := os.WriteFile(*outputPath, []byte(result.RawICS), 0o644); err != nil {
				return output.PrintError(err)
			}
			return 0
		}
		if _, err := os.Stdout.Write(append([]byte(result.RawICS), '\n')); err != nil {
			return output.PrintError(err)
		}
		return 0
	}

	return printNativeJSON(result, nil)
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
