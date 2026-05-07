package cli

import (
	"fmt"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/env"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/output"
)

func Run(args []string) int {
	if err := env.LoadLocalEnv(".env.local", ".env"); err != nil {
		return output.PrintError(err)
	}

	if len(args) == 0 {
		printRootUsage()
		return 1
	}

	switch args[0] {
	case "api":
		return runAPI(args[1:])
	case "portal":
		return runPortal(args[1:])
	case "alma":
		return runAlma(args[1:])
	case "ilias":
		return runIlias(args[1:])
	case "mail":
		return runMail(args[1:])
	case "moodle":
		return runMoodle(args[1:])
	case "timms":
		return runTimms(args[1:])
	case "discovery":
		return runDiscovery(args[1:])
	case "praxisportal":
		return runPraxisportal(args[1:])
	case "campus":
		return runCampus(args[1:])
	case "talks":
		return runTalks(args[1:])
	case "people":
		return runPeople(args[1:])
	case "-h", "--help", "help":
		printRootUsage()
		return 0
	default:
		return output.PrintError(fmt.Errorf("unknown command %q", args[0]))
	}
}

func printRootUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue api get /api/dashboard [--query key=value ...] [--output PATH] [--raw]")
	fmt.Println("  tue portal <dashboard|search|item|course-detail|health> ...")
	fmt.Println("  tue alma current-lectures [--date DD.MM.YYYY] [--limit N] [--json]")
	fmt.Println("  tue alma exams [--limit N|--query limit=N]")
	fmt.Println("  tue alma <timetable|enrollments|catalog|module-search|module-search-filters|module-detail|documents|studyservice|current-document|document|document-download-url|current-lectures-api|course-register|course-register-options|course-register-support|timetable-controls|timetable-view|timetable-pdf|portal-messages-feed|study-planner|course-search|catalog-page|studyservice-summary> ...")
	fmt.Println("  tue ilias search --term QUERY [--page N] [--json]")
	fmt.Println("  tue ilias info --target REF_ID_OR_URL [--json]")
	fmt.Println("  tue ilias <root|memberships|tasks|content|forum|exercise|search-api|search-options|info-api> ...")
	fmt.Println("  tue mail <mailboxes|inbox|message> ...")
	fmt.Println("  tue moodle <dashboard|calendar|courses|categories|category|category-courses|course|course-enrolment|course-enrol|grades|messages|notifications> ...")
	fmt.Println("  tue timms <search|suggest|item|streams|cite|tree> ...")
	fmt.Println("  tue discovery status [--raw]")
	fmt.Println("  tue praxisportal <filters|search|project> ...")
	fmt.Println("  tue campus <canteens|canteen|buildings|building-detail|events|kuf|seats> ...")
	fmt.Println("  tue talks <search|item> ...")
	fmt.Println("  tue people <search|action> ...")
}
