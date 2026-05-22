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
	case "alma":
		return runAlma(args[1:])
	case "ilias":
		return runIlias(args[1:])
	case "moodle":
		return runMoodle(args[1:])
	case "talks":
		return runTalks(args[1:])
	case "praxisportal":
		return runPraxisportal(args[1:])
	case "seatfinder":
		return runSeatfinder(args[1:])
	case "discovery":
		return runDiscovery(args[1:])
	case "-h", "--help", "help":
		printRootUsage()
		return 0
	default:
		return output.PrintError(fmt.Errorf("unknown command %q", args[0]))
	}
}

func printRootUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue alma current-lectures [--date DD.MM.YYYY] [--limit N] [--json]")
	fmt.Println("  tue alma exams [--limit N|--query limit=N]")
	fmt.Println("  tue alma timetable [--term TERM] [--query term=TERM] [--ics] [--output PATH] [--raw]")
	fmt.Println("  tue ilias search --term QUERY [--page N] [--json]")
	fmt.Println("  tue ilias info --target REF_ID_OR_URL [--json]")
	fmt.Println("  tue ilias <root|memberships|tasks|content|forum|exercise> [--query key=value ...]")
	fmt.Println("  tue ilias search-api --query term=QUERY [--query page=N]")
	fmt.Println("  tue ilias info-api --query target=REF_ID_OR_URL")
	fmt.Println("  tue moodle <dashboard|calendar|courses|categories|category|category-courses|course|course-enrolment|course-enrol|grades|messages|notifications> ...")
	fmt.Println("  tue talks <list|get> ...")
	fmt.Println("  tue praxisportal <filters|search|project> ...")
	fmt.Println("  tue seatfinder availability [--query location=ID] ...")
	fmt.Println("  tue discovery status [--raw]")
}
