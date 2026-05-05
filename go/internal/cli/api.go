package cli

import (
	"fmt"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/output"
)

func runAPI(args []string) int {
	if len(args) == 0 {
		printAPIUsage()
		return 1
	}

	switch args[0] {
	case "get":
		return runAPIGet(args[1:])
	case "-h", "--help", "help":
		printAPIUsage()
		return 0
	default:
		return output.PrintError(fmt.Errorf("unknown api command %q", args[0]))
	}
}

func runAPIGet(args []string) int {
	options, err := parseBackendRequestOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printAPIUsage()
			return 0
		}
		return output.PrintError(err)
	}
	if len(options.Positionals) != 1 {
		return output.PrintError(fmt.Errorf("api get expects exactly one backend path or URL"))
	}
	return executeBackendRequest(options.Positionals[0], "GET", options)
}

func printAPIUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue api get /api/dashboard --query term=Sommer\\ 2026")
	fmt.Println("  tue api get /api/alma/timetable/pdf --query term=Sommer\\ 2026 --output timetable.pdf")
	fmt.Println()
	fmt.Println("Flags:")
	fmt.Println("  --query key=value   Repeat to add query parameters")
	fmt.Println("  --output PATH       Write the response body to a file")
	fmt.Println("  --raw               Print JSON responses without pretty formatting")
}
