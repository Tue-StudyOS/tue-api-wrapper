package cli

import (
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/output"
)

type discoveryStatus struct {
	DocumentCount     int             `json:"document_count"`
	SemanticAvailable bool            `json:"semantic_available"`
	VectorStore       string          `json:"vector_store"`
	EmbeddingModel    *string         `json:"embedding_model"`
	LastRefresh       *string         `json:"last_refresh"`
	Facets            discoveryFacets `json:"facets"`
	Errors            []string        `json:"errors"`
	GeneratedAt       string          `json:"generated_at"`
}

type discoveryFacets struct {
	Sources     []discoveryFacetOption `json:"sources"`
	Kinds       []discoveryFacetOption `json:"kinds"`
	ModuleCodes []discoveryFacetOption `json:"module_codes"`
	Degrees     []discoveryFacetOption `json:"degrees"`
	Tags        []discoveryFacetOption `json:"tags"`
}

type discoveryFacetOption struct {
	Value string `json:"value"`
	Label string `json:"label"`
	Count int    `json:"count"`
}

func runDiscovery(args []string) int {
	if len(args) == 0 || args[0] == "-h" || args[0] == "--help" || args[0] == "help" {
		printDiscoveryUsage()
		if len(args) == 0 {
			return 1
		}
		return 0
	}

	switch args[0] {
	case "status":
		return runDiscoveryStatus(args[1:])
	case "search", "refresh":
		return output.PrintError(fmt.Errorf("tue discovery %s is not implemented natively in the Go CLI yet", args[0]))
	default:
		return output.PrintError(fmt.Errorf("unknown discovery command %q", args[0]))
	}
}

func printDiscoveryUsage() {
	fmt.Println("Usage:")
	fmt.Println("  tue discovery status [--raw]")
	fmt.Println()
	fmt.Println("Native discovery search and refresh are not implemented in the Go CLI yet.")
}

func runDiscoveryStatus(args []string) int {
	raw := false
	for _, arg := range args {
		switch arg {
		case "--raw":
			raw = true
		case "-h", "--help", "help":
			printDiscoveryUsage()
			return 0
		default:
			return output.PrintError(fmt.Errorf("unknown flag %q", arg))
		}
	}

	status := discoveryStatus{
		DocumentCount:     0,
		SemanticAvailable: false,
		VectorStore:       "native-go",
		Facets: discoveryFacets{
			Sources:     []discoveryFacetOption{},
			Kinds:       []discoveryFacetOption{},
			ModuleCodes: []discoveryFacetOption{},
			Degrees:     []discoveryFacetOption{},
			Tags:        []discoveryFacetOption{},
		},
		Errors:      []string{"native Go discovery index is not initialized"},
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
	}
	if raw {
		return printCompactJSON(status)
	}
	if err := output.PrintJSON(status); err != nil {
		return output.PrintError(err)
	}
	return 0
}

func printCompactJSON(value any) int {
	encoder := json.NewEncoder(os.Stdout)
	if err := encoder.Encode(value); err != nil {
		return output.PrintError(err)
	}
	return 0
}
