package cli

import (
	"flag"
	"fmt"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/config"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/env"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/ilias"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/output"
)

func runIlias(args []string) int {
	if len(args) == 0 {
		printIliasUsage()
		return 1
	}

	switch args[0] {
	case "search":
		return runIliasSearch(args[1:])
	case "info":
		return runIliasInfo(args[1:])
	case "root":
		return runIliasRoot(args[1:])
	case "memberships":
		return runIliasMemberships(args[1:])
	case "tasks":
		return runIliasTasks(args[1:])
	case "content":
		return runIliasContent(args[1:])
	case "forum":
		return runIliasForum(args[1:])
	case "exercise":
		return runIliasExercise(args[1:])
	case "search-api":
		return runIliasSearchAPI(args[1:])
	case "info-api":
		return runIliasInfoAPI(args[1:])
	case "-h", "--help", "help":
		printIliasUsage()
		return 0
	default:
		return output.PrintError(fmt.Errorf("unknown ilias command %q", args[0]))
	}
}

func printIliasUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue ilias search --term QUERY [--page N] [--json]")
	fmt.Println("  tue ilias info --target REF_ID_OR_URL [--json]")
	fmt.Println("  tue ilias <root|memberships|tasks|content|forum|exercise> [--query key=value ...] [--raw]")
	fmt.Println("  tue ilias search-api --query term=QUERY [--query page=N]")
	fmt.Println("  tue ilias info-api --query target=REF_ID_OR_URL")
}

func runIliasRoot(args []string) int {
	if len(args) != 0 {
		return output.PrintError(fmt.Errorf("usage: tue ilias root"))
	}
	client, ok := authenticatedIliasClient()
	if !ok {
		return 1
	}
	return printNativeJSON(client.FetchRootPage())
}

func runIliasMemberships(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printIliasUsage()
			return 0
		}
		return output.PrintError(err)
	}
	limit := 20
	if value := options.Query.Get("limit"); value != "" {
		limit, err = parsePositiveInt(value)
		if err != nil {
			return output.PrintError(fmt.Errorf("invalid limit query value %q", value))
		}
	}
	client, ok := authenticatedIliasClient()
	if !ok {
		return 1
	}
	return printNativeJSON(client.FetchMembershipOverview(limit))
}

func runIliasTasks(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printIliasUsage()
			return 0
		}
		return output.PrintError(err)
	}
	limit := 20
	if value := options.Query.Get("limit"); value != "" {
		limit, err = parsePositiveInt(value)
		if err != nil {
			return output.PrintError(fmt.Errorf("invalid limit query value %q", value))
		}
	}
	client, ok := authenticatedIliasClient()
	if !ok {
		return 1
	}
	return printNativeJSON(client.FetchTaskOverview(limit))
}

func runIliasContent(args []string) int {
	return runIliasTargetJSON(args, "content", func(client *ilias.Client, target string) (any, error) {
		return client.FetchContentPage(target)
	})
}

func runIliasForum(args []string) int {
	return runIliasTargetJSON(args, "forum", func(client *ilias.Client, target string) (any, error) {
		return client.FetchForumTopics(target)
	})
}

func runIliasExercise(args []string) int {
	return runIliasTargetJSON(args, "exercise", func(client *ilias.Client, target string) (any, error) {
		return client.FetchExerciseAssignments(target)
	})
}

func runIliasTargetJSON(args []string, command string, fetch func(*ilias.Client, string) (any, error)) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printIliasUsage()
			return 0
		}
		return output.PrintError(err)
	}
	target := options.Query.Get("target")
	if target == "" {
		return output.PrintError(fmt.Errorf("usage: tue ilias %s --query target=TARGET", command))
	}
	client, ok := authenticatedIliasClient()
	if !ok {
		return 1
	}
	return printNativeJSON(fetch(client, target))
}

func runIliasSearchAPI(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printIliasUsage()
			return 0
		}
		return output.PrintError(err)
	}
	term := options.Query.Get("term")
	if term == "" {
		return output.PrintError(fmt.Errorf("usage: tue ilias search-api --query term=QUERY"))
	}
	page := 1
	if value := options.Query.Get("page"); value != "" {
		page, err = parsePositiveInt(value)
		if err != nil || page == 0 {
			return output.PrintError(fmt.Errorf("invalid page query value %q", value))
		}
	}
	client, ok := authenticatedIliasClient()
	if !ok {
		return 1
	}
	return printNativeJSON(client.Search(term, page))
}

func runIliasInfoAPI(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printIliasUsage()
			return 0
		}
		return output.PrintError(err)
	}
	target := options.Query.Get("target")
	if target == "" {
		return output.PrintError(fmt.Errorf("usage: tue ilias info-api --query target=TARGET"))
	}
	client, ok := authenticatedIliasClient()
	if !ok {
		return 1
	}
	return printNativeJSON(client.FetchInfo(target))
}

func runIliasSearch(args []string) int {
	fs := flag.NewFlagSet("ilias search", flag.ContinueOnError)
	term := fs.String("term", "", "Search term")
	page := fs.Int("page", 1, "Page number")
	asJSON := fs.Bool("json", false, "Print JSON instead of text")
	if err := fs.Parse(args); err != nil {
		return 1
	}

	client, ok := authenticatedIliasClient()
	if !ok {
		return 1
	}

	result, err := client.Search(*term, *page)
	if err != nil {
		return output.PrintError(err)
	}
	if *asJSON {
		if err := output.PrintJSON(result); err != nil {
			return output.PrintError(err)
		}
		return 0
	}

	fmt.Printf("Query: %s\n", result.Query)
	fmt.Printf("Page: %d\n", result.PageNumber)
	fmt.Printf("Results: %d\n", len(result.Results))
	for index, item := range result.Results {
		fmt.Printf("%02d. %s\n", index+1, item.Title)
		if item.URL != nil {
			fmt.Printf("    %s\n", *item.URL)
		}
	}
	return 0
}

func runIliasInfo(args []string) int {
	fs := flag.NewFlagSet("ilias info", flag.ContinueOnError)
	target := fs.String("target", "", "Numeric ref_id or full info URL")
	asJSON := fs.Bool("json", false, "Print JSON instead of text")
	if err := fs.Parse(args); err != nil {
		return 1
	}

	client, ok := authenticatedIliasClient()
	if !ok {
		return 1
	}

	page, err := client.FetchInfo(*target)
	if err != nil {
		return output.PrintError(err)
	}
	if *asJSON {
		if err := output.PrintJSON(page); err != nil {
			return output.PrintError(err)
		}
		return 0
	}

	fmt.Println(page.Title)
	for _, section := range page.Sections {
		fmt.Printf("\n[%s]\n", section.Title)
		for _, field := range section.Fields {
			label := "-"
			if field.Label != nil {
				label = *field.Label
			}
			fmt.Printf("%s: %s\n", label, field.Value)
		}
	}
	return 0
}

func authenticatedIliasClient() (*ilias.Client, bool) {
	username, password := env.IliasCredentials()
	if username == "" || password == "" {
		output.PrintError(fmt.Errorf(
			"set UNI_USERNAME and UNI_PASSWORD before using authenticated commands; legacy ALMA_* and ILIAS_* env vars are still supported as fallbacks",
		))
		return nil, false
	}

	client, err := ilias.NewClient(config.DefaultTimeout())
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
