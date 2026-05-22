package cli

import (
	"fmt"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/config"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/output"
	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/seatfinder"
)

func runSeatfinder(args []string) int {
	if len(args) == 0 || args[0] == "-h" || args[0] == "--help" || args[0] == "help" {
		printSeatfinderUsage()
		if len(args) == 0 {
			return 1
		}
		return 0
	}

	switch args[0] {
	case "availability":
		return runSeatfinderAvailability(args[1:])
	default:
		return output.PrintError(fmt.Errorf("unknown seatfinder command %q", args[0]))
	}
}

func printSeatfinderUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue seatfinder availability [--query location=UBH1] [--query location=UBB2] [--raw]")
}

func runSeatfinderAvailability(args []string) int {
	options, err := parseQueryOptions(args)
	if err != nil {
		if err == errUsageRequested {
			printSeatfinderUsage()
			return 0
		}
		return output.PrintError(err)
	}

	locations := options.Query["location"]
	if len(locations) == 0 {
		locations = seatfinder.DefaultLocations()
	} else {
		for idx, value := range locations {
			locations[idx] = strings.TrimSpace(value)
		}
	}

	client := seatfinder.New(config.DefaultTimeout())
	return printNativeJSON(client.FetchAvailability(locations))
}
