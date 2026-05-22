package cli

import (
	"fmt"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/config"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/output"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/praxisportal"
)

func runPraxisportal(args []string) int {
	if len(args) == 0 || args[0] == "-h" || args[0] == "--help" || args[0] == "help" {
		printPraxisportalUsage()
		if len(args) == 0 {
			return 1
		}
		return 0
	}

	switch args[0] {
	case "filters":
		return runPraxisportalFilters(args[1:])
	case "search":
		return runPraxisportalSearch(args[1:])
	case "project":
		return runPraxisportalProject(args[1:])
	default:
		return output.PrintError(fmt.Errorf("unknown praxisportal command %q", args[0]))
	}
}

func printPraxisportalUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue praxisportal filters")
	fmt.Println("  tue praxisportal search [--query query=TEXT] [--query project_type_id=N] [--query industry_id=N] [--query page=N] [--query per_page=N] [--query sort=newest] [--raw]")
	fmt.Println("  tue praxisportal project <project_id>")
	fmt.Println("  tue praxisportal project --query id=PROJECT_ID")
}

func runPraxisportalFilters(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printPraxisportalUsage()
			return 0
		}
		return output.PrintError(err)
	}
	if len(options.Positionals) != 0 {
		return output.PrintError(fmt.Errorf("usage: tue praxisportal filters"))
	}
	client := praxisportal.New(config.DefaultTimeout())
	return printNativeJSON(client.FetchFilterOptions())
}

func runPraxisportalSearch(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printPraxisportalUsage()
			return 0
		}
		return output.PrintError(err)
	}
	query := options.Query.Get("query")

	projectTypeIDs, err := parseIntList(options.Query["project_type_id"])
	if err != nil {
		return output.PrintError(fmt.Errorf("invalid project_type_id query value: %w", err))
	}
	industryIDs, err := parseIntList(options.Query["industry_id"])
	if err != nil {
		return output.PrintError(fmt.Errorf("invalid industry_id query value: %w", err))
	}

	page := 0
	if rawPage := options.Query.Get("page"); rawPage != "" {
		page, err = parsePositiveInt(rawPage)
		if err != nil {
			return output.PrintError(fmt.Errorf("invalid page query value %q", rawPage))
		}
	}

	perPage := 20
	if rawPerPage := options.Query.Get("per_page"); rawPerPage != "" {
		perPage, err = parsePositiveInt(rawPerPage)
		if err != nil || perPage == 0 {
			return output.PrintError(fmt.Errorf("invalid per_page query value %q", rawPerPage))
		}
	}

	sort := strings.TrimSpace(options.Query.Get("sort"))

	client := praxisportal.New(config.DefaultTimeout())
	return printNativeJSON(client.SearchProjects(query, projectTypeIDs, industryIDs, page, perPage, sort))
}

func runPraxisportalProject(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printPraxisportalUsage()
			return 0
		}
		return output.PrintError(err)
	}
	projectID := options.Query.Get("id")
	if projectID == "" && len(options.Positionals) == 1 {
		projectID = options.Positionals[0]
	}
	if projectID == "" {
		return output.PrintError(fmt.Errorf("usage: tue praxisportal project <project_id>"))
	}
	parsed, err := parsePositiveInt(projectID)
	if err != nil || parsed == 0 {
		return output.PrintError(fmt.Errorf("invalid project id %q", projectID))
	}
	client := praxisportal.New(config.DefaultTimeout())
	return printNativeJSON(client.FetchProject(parsed))
}
