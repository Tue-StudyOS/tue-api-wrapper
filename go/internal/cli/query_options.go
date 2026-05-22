package cli

import (
	"fmt"
	"net/url"
	"strings"
)

type queryOptions struct {
	Query       url.Values
	Positionals []string
}

func parseQueryOptions(args []string) (queryOptions, error) {
	options := queryOptions{Query: url.Values{}}

	for index := 0; index < len(args); index++ {
		arg := args[index]
		switch {
		case arg == "-h" || arg == "--help" || arg == "help":
			return options, errUsageRequested
		case arg == "--raw":
			// accepted for CLI compatibility; native commands can decide how to render JSON
		case arg == "--query":
			index++
			if index >= len(args) {
				return options, fmt.Errorf("--query requires key=value")
			}
			if err := addQuery(options.Query, args[index]); err != nil {
				return options, err
			}
		case strings.HasPrefix(arg, "--query="):
			if err := addQuery(options.Query, strings.TrimPrefix(arg, "--query=")); err != nil {
				return options, err
			}
		default:
			if strings.HasPrefix(arg, "-") {
				return options, fmt.Errorf("unknown flag %q", arg)
			}
			options.Positionals = append(options.Positionals, arg)
		}
	}

	return options, nil
}

func addQuery(values url.Values, item string) error {
	key, value, ok := strings.Cut(item, "=")
	if !ok || strings.TrimSpace(key) == "" {
		return fmt.Errorf("query values must use key=value, got %q", item)
	}
	values.Add(strings.TrimSpace(key), value)
	return nil
}

var errUsageRequested = fmt.Errorf("usage requested")
