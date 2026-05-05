package cli

var talksRoutes = map[string]backendRoute{
	"search": {
		Path:        "/api/talks",
		Description: "Talk calendar search. Optional queries: query, limit.",
	},
	"item": {
		Path:        "/api/talks/{talk_id}",
		PathArgs:    []string{"talk_id"},
		Description: "Single talk detail.",
	},
}

func runTalks(args []string) int {
	return runBackendGroup("talks", args, talksRoutes)
}
