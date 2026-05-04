package cli

var peopleRoutes = map[string]backendRoute{
	"search": {
		Path:        "/api/people/search",
		Description: "University directory search. Use --query query=....",
	},
	"action": {
		Method:      "POST",
		Path:        "/api/people/action",
		Description: "Prepare a directory action payload. Pass backend query parameters directly.",
	},
}

func runPeople(args []string) int {
	return runBackendGroup("people", args, peopleRoutes)
}
