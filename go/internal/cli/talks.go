package cli

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/config"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/output"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/talks"
)

func runTalks(args []string) int {
	if len(args) == 0 || args[0] == "-h" || args[0] == "--help" || args[0] == "help" {
		printTalksUsage()
		if len(args) == 0 {
			return 1
		}
		return 0
	}

	switch args[0] {
	case "list":
		return runTalksList(args[1:])
	case "get":
		return runTalksGet(args[1:])
	default:
		return output.PrintError(fmt.Errorf("unknown talks command %q", args[0]))
	}
}

func printTalksUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue talks list [--query scope=upcoming|previous] [--query query=TEXT] [--query tag_id=N] [--query include_disabled=true] [--query limit=N] [--raw]")
	fmt.Println("  tue talks get <talk_id>")
	fmt.Println("  tue talks get --query id=TALK_ID")
}

func runTalksList(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printTalksUsage()
			return 0
		}
		return output.PrintError(err)
	}

	scope := strings.TrimSpace(options.Query.Get("scope"))
	query := options.Query.Get("query")
	includeDisabled := parseBool(options.Query.Get("include_disabled"))
	limit := 24
	if rawLimit := options.Query.Get("limit"); rawLimit != "" {
		limit, err = parsePositiveInt(rawLimit)
		if err != nil || limit == 0 {
			return output.PrintError(fmt.Errorf("invalid limit query value %q", rawLimit))
		}
	}

	tagIDs, err := parseIntList(options.Query["tag_id"])
	if err != nil {
		return output.PrintError(fmt.Errorf("invalid tag_id query value: %w", err))
	}

	client := talks.New(config.DefaultTimeout())
	items, err := client.FetchTalks(scope)
	if err != nil {
		return output.PrintError(err)
	}
	return printNativeJSON(talks.BuildResponse(items, scope, query, tagIDs, includeDisabled, limit), nil)
}

func runTalksGet(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printTalksUsage()
			return 0
		}
		return output.PrintError(err)
	}

	talkID := options.Query.Get("id")
	if talkID == "" && len(options.Positionals) == 1 {
		talkID = options.Positionals[0]
	}
	if talkID == "" {
		return output.PrintError(fmt.Errorf("usage: tue talks get <talk_id>"))
	}
	parsed, err := parsePositiveInt(talkID)
	if err != nil || parsed == 0 {
		return output.PrintError(fmt.Errorf("invalid talk id %q", talkID))
	}

	client := talks.New(config.DefaultTimeout())
	return printNativeJSON(client.FetchTalk(parsed))
}

func parseIntList(values []string) ([]int, error) {
	if len(values) == 0 {
		return nil, nil
	}
	parsed := make([]int, 0, len(values))
	for _, value := range values {
		value = strings.TrimSpace(value)
		if value == "" {
			continue
		}
		number, err := strconv.Atoi(value)
		if err != nil {
			return nil, err
		}
		parsed = append(parsed, number)
	}
	return parsed, nil
}

func parseBool(value string) bool {
	value = strings.TrimSpace(strings.ToLower(value))
	switch value {
	case "true", "1", "yes", "y":
		return true
	default:
		return false
	}
}
